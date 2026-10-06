"""CTF vs JT (PLMXML) identity cross-checks.

The JT wrapper carries identification only (item id, revision, product name, bounding box), so
these checks confirm that the CTF was written for the same part the JT file represents. It holds no
per-characteristic data, so tolerances cannot be compared against it.
"""
import re
from dataclasses import asdict, dataclass

from app.pipeline.parsing.ctf_parser import ParsedCtf
from app.pipeline.parsing.plmxml_parser import PlmMeta

DRAWING_ID_RE = re.compile(r"FC00[A-Z]{3}\d{5}", re.IGNORECASE)
PSA_REF_RE = re.compile(r"(?<![A-Za-z0-9])\d{8}[A-Z]{2}(?![A-Za-z0-9])")


@dataclass
class Check:
    id: str
    field: str
    ctf_value: str | None
    jt_value: str | None
    status: str  # pass | fail | warn | info
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


def _canon(v: str | None) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", (v or "").upper()).strip()


def compare(ctf: ParsedCtf, jt: PlmMeta) -> list[Check]:
    f = ctf.front
    checks: list[Check] = []

    # JT001 drawing reference <-> JT item id
    drawing = f.get("drawing_ref")
    ids = DRAWING_ID_RE.findall(drawing or "")
    if not drawing:
        checks.append(Check("JT001", "Drawing reference vs JT item id", None, jt.item_id, "fail", "CTF front page has no drawing reference"))
    elif not jt.item_id:
        checks.append(Check("JT001", "Drawing reference vs JT item id", drawing, None, "warn", "JT file has no item id"))
    elif ids and ids[0].upper() == jt.item_id.upper() and len(ids) == 1:
        extra = drawing.strip().upper() != ids[0].upper()
        checks.append(Check("JT001", "Drawing reference vs JT item id", drawing, jt.item_id, "warn" if extra else "pass",
                            "matches, but the field also holds other text (expected only the drawing id)" if extra else "match"))
    else:
        checks.append(Check("JT001", "Drawing reference vs JT item id", drawing, jt.item_id, "fail",
                            f"CTF drawing reference {'contains ' + ids[0] if ids else 'has no FC00 drawing id'}; JT item id is {jt.item_id}"))

    # JT002 stale PSA reference inside the drawing reference
    part_ref = f.get("part_ref")
    stray = [m for m in PSA_REF_RE.findall(drawing or "") if m != part_ref]
    if stray:
        checks.append(Check("JT002", "Drawing reference contents", drawing, None, "warn",
                            f"drawing reference contains PSA reference {stray[0]}, which is not this CTF's part reference ({part_ref})"))

    # JT003 part name
    a, b = _canon(f.get("part_name")), _canon(jt.product_name)
    if not f.get("part_name"):
        st, msg = "fail", "CTF front page has no part name"
    elif not jt.product_name:
        st, msg = "info", "JT product name not in the expected '<item>_<rev>-<name>__PART' form; cannot compare"
    elif a == b:
        st, msg = "pass", "match"
    elif a in b or b in a:
        st, msg = "warn", "names overlap but are not identical"
    else:
        st, msg = "fail", "part names differ"
    checks.append(Check("JT003", "Part name", f.get("part_name"), jt.product_name, st, msg))

    # JT004 revision / indice
    ind = f.get("drawing_indice")
    if not ind:
        checks.append(Check("JT004", "Drawing indice vs JT revision", None, jt.revision, "warn", "CTF drawing indice is empty; cannot confirm the JT revision"))
    elif _canon(ind) == _canon(jt.revision):
        checks.append(Check("JT004", "Drawing indice vs JT revision", ind, jt.revision, "pass", "match"))
    else:
        checks.append(Check("JT004", "Drawing indice vs JT revision", ind, jt.revision, "info",
                            "formats differ (CTF letter index vs Teamcenter revision); confirm manually"))

    # JT005 what the JT cannot confirm
    checks.append(Check("JT005", "Part reference", part_ref, None, "info", "PSA part reference is not present in the JT file; not verifiable"))
    return checks


def summarize(checks: list[Check]) -> dict:
    counts = {s: sum(c.status == s for c in checks) for s in ("pass", "fail", "warn", "info")}
    verdict = "fail" if counts["fail"] else "review" if counts["warn"] else "pass"
    return {"verdict": verdict, **counts}
