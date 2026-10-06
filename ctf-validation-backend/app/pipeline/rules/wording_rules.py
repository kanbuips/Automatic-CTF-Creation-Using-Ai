"""Wording rules."""
import re

from app.pipeline.constants import PLACEHOLDER_RE
from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding, cid

MIN_DESC_LEN = 3


def check(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    out: list[RuleFinding] = []
    for i, c in enumerate(parsed.characteristics):
        ref = cid(c, i)
        desc = c.description
        if desc is None or not desc.strip():
            out.append(RuleFinding("WRD001", "warning", "Description is empty", ref))
            continue
        if PLACEHOLDER_RE.search(desc):
            out.append(RuleFinding("WRD002", "error", "Description contains a placeholder (TBD/TODO/???)", ref))
        elif len(desc.strip()) < MIN_DESC_LEN:
            out.append(RuleFinding("WRD004", "warning", f"Description {desc.strip()!r} is too short", ref))
        if desc != desc.strip() or re.search(r"\s{2,}", desc):
            out.append(RuleFinding("WRD003", "info", "Description has leading/trailing or repeated whitespace", ref))
    return out
