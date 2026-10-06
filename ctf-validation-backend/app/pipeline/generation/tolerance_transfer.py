"""Fill a CTF-PIS template's specification limits from a previous CTF.

The template (new CTF in the current corporate format) keeps its structure, macros, styles and
validations: only the nominal / lower / upper limit cells (columns P, Q, R) are rewritten, by
patching the sheet XML inside the .xlsm. IT-/IT+ are formulas in the template; their cached values
are refreshed and the workbook is flagged to recalculate on open.

Matching is intentionally strict. Wording similarity between different parts is not evidence that
two characteristics share tolerances, so a template row is only filled when a *key* matches:
(characteristic kind = first word of the wording, datum letter) within the same Type, and every
matching source row agrees on the values. Everything else is reported and left untouched; pairings
can be forced with `overrides` ({template_code: source_code}).
"""
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.core.exceptions import UnprocessableError
from app.pipeline.parsing.ctf_parser import CTF_SHEET, CtfRow, ParsedCtf, parse_ctf

DATUM_RE = re.compile(r"\bdatum\s+([A-Z])\b", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-z]+")
DECIMALS = 9

Values = tuple[float | None, float | None, float | None]  # nominal, lsl, usl


@dataclass
class RowPlan:
    code: str
    wording: str | None
    status: str  # updated | unchanged | ambiguous | no_match | no_key | unit_mismatch | formula_cell
    manual: bool = False
    source_codes: list[str] = field(default_factory=list)
    old: Values = (None, None, None)
    new: Values | None = None
    note: str = ""


@dataclass
class TransferResult:
    plan: list[RowPlan]
    output: Path | None = None

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for p in self.plan:
            out[p.status] = out.get(p.status, 0) + 1
        out["total"] = len(self.plan)
        return out

    def as_dicts(self) -> list[dict]:
        return [asdict(p) for p in self.plan]


def _values(r: CtfRow) -> Values:
    return (r.nominal, r.lsl, r.usl)


def _key(r: CtfRow) -> tuple[str, str] | None:
    """(kind, datum) or None when the wording doesn't carry a usable key."""
    m, w = DATUM_RE.search(r.wording or ""), WORD_RE.search(r.wording or "")
    if not (m and w):
        return None
    return (w.group(0).lower(), m.group(1).upper())


def _rounded(v: Values) -> Values:
    return tuple(None if x is None else round(x, DECIMALS) for x in v)  # type: ignore[return-value]


def build_plan(template: ParsedCtf, source: ParsedCtf, overrides: dict[str, str] | None = None) -> list[RowPlan]:
    overrides = overrides or {}
    by_code = {r.code: r for r in source.rows}
    unknown = [c for c in overrides.values() if c not in by_code]
    if unknown:
        raise UnprocessableError(f"Override source code(s) not found in the previous CTF: {', '.join(unknown)}")
    unknown_t = [c for c in overrides if c not in {r.code for r in template.rows}]
    if unknown_t:
        raise UnprocessableError(f"Override template code(s) not found in the new CTF: {', '.join(unknown_t)}")

    plan: list[RowPlan] = []
    for t in template.rows:
        p = RowPlan(code=t.code, wording=t.wording, status="no_match", old=_values(t))
        if t.code in overrides:
            cands, p.manual = [by_code[overrides[t.code]]], True
        else:
            key = _key(t)
            if key is None:
                p.status, p.note = "no_key", "wording has no datum, so no safe match to a previous characteristic"
                plan.append(p)
                continue
            cands = [s for s in source.rows if s.type == t.type and _key(s) == key]
            if not cands:
                p.note = f"no previous {t.type or ''} row with kind '{key[0]}' and datum {key[1]}".replace("  ", " ")
                plan.append(p)
                continue
        p.source_codes = [c.code for c in cands]
        if any(c.unit != t.unit for c in cands):
            p.status, p.note = "unit_mismatch", f"unit differs (template {t.unit!r})"
        elif len({_rounded(_values(c)) for c in cands}) > 1:
            p.status = "ambiguous"
            p.note = "previous rows disagree: " + "; ".join(f"{c.code} {_values(c)}" for c in cands)
        elif any(v is None for v in _values(cands[0])):
            p.status, p.note = "no_match", f"previous row {cands[0].code} has no numeric limits"
        else:
            p.new = _rounded(_values(cands[0]))
            p.status = "unchanged" if p.new == _rounded(p.old) else "updated"
        plan.append(p)
    return plan


# ---------------------------------------------------------------------------------------------
# XML patching
# ---------------------------------------------------------------------------------------------
def _sheet_path(z: zipfile.ZipFile, sheet_name: str) -> str:
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    escaped = sheet_name.replace("&", "&amp;")
    m = re.search(r'<sheet\b[^>]*\bname="%s"[^>]*>' % re.escape(escaped), wb)
    rid = re.search(r'r:id="([^"]+)"', m.group(0)) if m else None
    if not rid:
        raise UnprocessableError(f"Template has no '{sheet_name}' sheet")
    for rel in re.findall(r"<Relationship\b[^>]*>", rels):
        if f'Id="{rid.group(1)}"' in rel:
            target = re.search(r'Target="([^"]+)"', rel).group(1)
            return target.lstrip("/") if target.startswith("/") else "xl/" + target
    raise UnprocessableError(f"Cannot resolve the '{sheet_name}' sheet part")


def _fmt(v: float) -> str:
    text = repr(round(v, DECIMALS) + 0.0)
    return text[:-2] if text.endswith(".0") else text


def _row_span(xml: str, r: int) -> tuple[int, int] | None:
    m = re.search(r'<row r="%d"[ >]' % r, xml)
    if not m:
        return None
    end = xml.find("</row>", m.start())
    return (m.start(), end + len("</row>")) if end != -1 else None


def _cell_re(ref: str):
    return re.compile(r'<c r="%s"((?:\s[^>]*?)?)(?:/>|>(.*?)</c>)' % ref, re.S)


def _set_cell(row_xml: str, ref: str, value: float, *, cached_only: bool = False) -> tuple[str, bool]:
    """Write a numeric value. Returns (new_row_xml, applied). Formula cells are only touched when
    cached_only (their <f> is kept and just the cached <v> refreshed)."""
    m = _cell_re(ref).search(row_xml)
    if not m:
        return row_xml, False
    attrs, inner = m.group(1), m.group(2) or ""
    has_formula = "<f" in inner
    if has_formula != cached_only:
        return row_xml, False
    attrs = re.sub(r'\st="[^"]*"', "", attrs)
    formula = re.search(r"<f\b.*?(?:/>|</f>)", inner, re.S).group(0) if has_formula else ""
    new = f'<c r="{ref}"{attrs}>{formula}<v>{_fmt(value)}</v></c>'
    return row_xml[: m.start()] + new + row_xml[m.end() :], True


def apply_plan(template_path: Path, plan: list[RowPlan], rows_by_code: dict[str, int], out_path: Path) -> None:
    letters = {"nominal": "P", "lsl": "Q", "usl": "R"}
    with zipfile.ZipFile(template_path) as zin:
        sheet = _sheet_path(zin, CTF_SHEET)
        xml = zin.read(sheet).decode("utf-8")
        for p in plan:
            if p.status != "updated" or p.new is None:
                continue
            r = rows_by_code[p.code]
            span = _row_span(xml, r)
            if span is None:
                p.status, p.note = "formula_cell", "row not present in the sheet XML"
                continue
            row_xml = xml[span[0] : span[1]]
            nominal, lsl, usl = p.new
            done = True
            for letter, val in zip(letters.values(), p.new):
                row_xml, ok = _set_cell(row_xml, f"{letter}{r}", val)
                done &= ok
            if not done:
                p.status, p.note = "formula_cell", "a limit cell is a formula or missing; left unchanged"
                continue
            row_xml, _ = _set_cell(row_xml, f"S{r}", lsl - nominal, cached_only=True)
            row_xml, _ = _set_cell(row_xml, f"T{r}", usl - nominal, cached_only=True)
            xml = xml[: span[0]] + row_xml + xml[span[1] :]

        with zipfile.ZipFile(out_path, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == sheet:
                    data = xml.encode("utf-8")
                elif item.filename == "xl/workbook.xml":
                    text = data.decode("utf-8")
                    if "fullCalcOnLoad" not in text:
                        text = re.sub(r"<calcPr\b", '<calcPr fullCalcOnLoad="1"', text, count=1)
                    data = text.encode("utf-8")
                zout.writestr(item, data, compress_type=item.compress_type)


def transfer_tolerances(
    template_path: str | Path,
    source_path: str | Path,
    out_path: str | Path,
    overrides: dict[str, str] | None = None,
) -> TransferResult:
    template, source = parse_ctf(template_path), parse_ctf(source_path)
    plan = build_plan(template, source, overrides)
    out = Path(out_path)
    apply_plan(Path(template_path), plan, {r.code: r.row for r in template.rows}, out)
    return TransferResult(plan, out)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("template", help="new CTF-PIS workbook (format to keep)")
    ap.add_argument("source", help="previous CTF-PIS workbook (tolerances to take)")
    ap.add_argument("out", help="output .xlsm")
    ap.add_argument("--map", action="append", default=[], metavar="NEW=OLD", help="force a pairing, e.g. 01A02=01A05")
    args = ap.parse_args()
    overrides = dict(m.split("=", 1) for m in args.map)
    result = transfer_tolerances(args.template, args.source, args.out, overrides)
    for p in result.plan:
        print(f"{p.code:8} {p.status:14} {p.old} -> {p.new} {p.source_codes} {p.note}")
    print(result.summary())


if __name__ == "__main__":
    main()
