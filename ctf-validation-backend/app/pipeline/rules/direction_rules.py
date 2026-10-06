"""Direction rules."""
from app.pipeline.constants import VALID_DIRECTIONS
from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding, cid


def check(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    out: list[RuleFinding] = []
    for i, c in enumerate(parsed.characteristics):
        ref = cid(c, i)
        d = (c.direction or "").strip()
        if not d:
            out.append(RuleFinding("DIR001", "error", "Direction is missing", ref))
        elif d.upper() not in VALID_DIRECTIONS:
            out.append(
                RuleFinding("DIR002", "error", f"Direction {d!r} is invalid (allowed: {', '.join(sorted(VALID_DIRECTIONS))})", ref)
            )
        elif d != d.upper():
            out.append(RuleFinding("DIR003", "info", f"Direction {d!r} should be upper case", ref))
    return out
