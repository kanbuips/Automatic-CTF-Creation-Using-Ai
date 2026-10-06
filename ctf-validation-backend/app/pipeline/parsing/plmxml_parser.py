"""Parsing of the Teamcenter Visualization PLMXML that wraps a JT file (identity data only)."""
import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from app.core.exceptions import UnprocessableError

NAME_RE = re.compile(r"^(?P<item>[A-Za-z0-9]+)_(?P<rev>\d+(?:_\d+)*)-(?P<name>.*?)(?:__PART)?$")


@dataclass
class PlmMeta:
    item_id: str | None
    revision: str | None
    object_name: str | None
    product_name: str | None  # part name as embedded in the ProductInstance name
    instance_name: str | None
    bounds: list[float] | None = None


def _local(el) -> str:
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def parse_plmxml_bytes(data: bytes) -> PlmMeta:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, remove_comments=True)
    try:
        root = etree.fromstring(data, parser)
    except etree.XMLSyntaxError as exc:
        raise UnprocessableError(f"Invalid PLMXML: {exc}") from exc
    if _local(root) != "PLMXML":
        raise UnprocessableError("Not a PLMXML file (root element is not PLMXML)")

    values: dict[str, str] = {}
    instance = bound = None
    for el in root.iter():
        name = _local(el)
        if name == "UserValue" and el.get("title") and el.get("value") is not None:
            values.setdefault(el.get("title"), el.get("value"))
        elif name == "ProductInstance" and instance is None:
            instance = el.get("name")
        elif name == "Bound" and bound is None:
            bound = el.get("values")

    inst_name = instance
    m = NAME_RE.match(inst_name) if inst_name else None
    item = values.get("PLMItemIdStr") or (m.group("item") if m else None)
    rev = values.get("PLMRevisionStr") or (m.group("rev").replace("_", ".") if m else None)
    if not (item or inst_name):
        raise UnprocessableError("PLMXML has no part identification (PLMItemIdStr / ProductInstance)")
    try:
        bounds = [float(x) for x in bound.split()] if bound else None
    except ValueError:
        bounds = None
    return PlmMeta(
        item_id=item,
        revision=rev,
        object_name=values.get("PLMObjectName"),
        product_name=m.group("name").strip() if m else None,
        instance_name=inst_name,
        bounds=bounds,
    )


def parse_plmxml(path: str | Path) -> PlmMeta:
    return parse_plmxml_bytes(Path(path).read_bytes())
