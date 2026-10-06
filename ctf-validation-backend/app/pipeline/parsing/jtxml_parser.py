"""lxml parsing of JTXML.

The parser is deliberately tolerant about the schema: a field may be an attribute or a child
element, and several common aliases are accepted (e.g. UpperTol / TolPlus / Upper).
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from app.core.exceptions import UnprocessableError

CHAR_TAGS = {"characteristic", "feature", "dimension", "measurement"}
FIELD_ALIASES = {
    "id": ("id", "ref", "number", "no"),
    "name": ("name", "label", "title"),
    "nominal": ("nominal", "nom", "target"),
    "upper": ("uppertol", "tolplus", "upper", "plus"),
    "lower": ("lowertol", "tolminus", "lower", "minus"),
    "unit": ("unit", "units"),
    "direction": ("direction", "dir", "axis"),
    "description": ("description", "desc", "text", "wording"),
}
HEADER_ALIASES = {
    "part_name": ("partname", "part"),
    "model_name": ("modelname", "model"),
    "template_version": ("templateversion", "template", "templaterev"),
}
_NUM_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


@dataclass
class Characteristic:
    id: str | None
    name: str | None = None
    nominal: float | None = None
    upper_tol: float | None = None
    lower_tol: float | None = None
    unit: str | None = None
    direction: str | None = None
    description: str | None = None
    raw_nominal: str | None = None


@dataclass
class ParsedJtxml:
    part_name: str | None
    model_name: str | None
    template_version: str | None
    characteristics: list[Characteristic] = field(default_factory=list)


def _norm(s: str) -> str:
    return re.sub(r"[_\-\s]", "", s.lower())


def _local(el) -> str:
    return _norm(etree.QName(el).localname) if isinstance(el.tag, str) else ""


def _get(el, names: tuple[str, ...], *, children: bool = True) -> str | None:
    for key, val in el.attrib.items():
        if _norm(etree.QName(key).localname) in names:
            return val.strip()
    if children:
        for child in el:
            if _local(child) in names:
                return (child.text or "").strip()
    return None


def _to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    t = raw.strip().replace("−", "-").replace(",", ".")
    t = t.lstrip("±")
    return float(t) if _NUM_RE.fullmatch(t) else None


def _tolerances(upper_raw: str | None, lower_raw: str | None):
    upper, lower = _to_float(upper_raw), _to_float(lower_raw)
    if upper_raw and upper_raw.strip().startswith("±") and lower_raw is None and upper is not None:
        return abs(upper), -abs(upper)
    return upper, lower


def _parse_characteristic(el) -> Characteristic:
    raw = {key: _get(el, aliases) for key, aliases in FIELD_ALIASES.items()}
    upper, lower = _tolerances(raw["upper"], raw["lower"])
    return Characteristic(
        id=raw["id"] or None,
        name=raw["name"] or None,
        nominal=_to_float(raw["nominal"]),
        upper_tol=upper,
        lower_tol=lower,
        unit=raw["unit"] or None,
        direction=raw["direction"] or None,
        description=raw["description"] if raw["description"] is not None else None,
        raw_nominal=raw["nominal"],
    )


def parse_jtxml_bytes(data: bytes) -> ParsedJtxml:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False, remove_comments=True)
    try:
        root = etree.fromstring(data, parser)
    except etree.XMLSyntaxError as exc:
        raise UnprocessableError(f"Invalid JTXML: {exc}") from exc

    header: dict[str, str | None] = {k: None for k in HEADER_ALIASES}
    for el in root.iter():
        if not isinstance(el.tag, str) or _local(el) in CHAR_TAGS:
            continue
        for key, aliases in HEADER_ALIASES.items():
            if header[key] is None:
                is_leaf = len(el) == 0
                val = (el.text or "").strip() if _local(el) in aliases and is_leaf else _get(el, aliases, children=False)
                if val:
                    header[key] = val

    chars = [_parse_characteristic(el) for el in root.iter() if isinstance(el.tag, str) and _local(el) in CHAR_TAGS]
    if not chars:
        raise UnprocessableError("JTXML contains no characteristics")
    return ParsedJtxml(characteristics=chars, **header)


def parse_jtxml(path: str | Path) -> ParsedJtxml:
    return parse_jtxml_bytes(Path(path).read_bytes())
