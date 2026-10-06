"""Template rules: Beta 3 enforced, Beta 2 rejected."""
import re

from app.core.config import get_settings
from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding


def _canon(v: str) -> str:
    return re.sub(r"[\s_\-]", "", v).lower()


def check(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    s = settings or get_settings()
    version = parsed.template_version
    if not version:
        return [RuleFinding("TPL002", "error", f"Template version is missing ({s.required_template} is required)")]
    if _canon(version) in {_canon(r) for r in s.rejected_templates}:
        return [RuleFinding("TPL001", "critical", f"Template {version!r} is rejected; use {s.required_template}")]
    if _canon(version) != _canon(s.required_template):
        return [RuleFinding("TPL003", "error", f"Template {version!r} is not supported; use {s.required_template}")]
    return []
