"""Part name / model name checks."""
import re

from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding

NAME_RE = re.compile(r"[A-Za-z0-9 _\-./()]+")


def _check_name(label: str, code: str, value: str | None) -> list[RuleFinding]:
    if not value or not value.strip():
        return [RuleFinding(f"{code}1", "error", f"{label} is missing")]
    out = []
    if not NAME_RE.fullmatch(value):
        out.append(RuleFinding(f"{code}2", "error", f"{label} {value!r} contains invalid characters"))
    if value != value.strip() or "  " in value:
        out.append(RuleFinding(f"{code}3", "info", f"{label} has leading/trailing or repeated whitespace"))
    return out


def check(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    return _check_name("Part name", "NAMP", parsed.part_name) + _check_name("Model name", "NAMM", parsed.model_name)
