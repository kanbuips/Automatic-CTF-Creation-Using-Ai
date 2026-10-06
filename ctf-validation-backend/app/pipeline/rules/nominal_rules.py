"""Nominal rules."""
from collections import defaultdict

from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding, cid


def check(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    out: list[RuleFinding] = []
    seen_ids: dict[str, int] = defaultdict(int)
    by_key: dict[tuple, set[float]] = defaultdict(set)

    for i, c in enumerate(parsed.characteristics):
        ref = cid(c, i)
        if c.id is None:
            out.append(RuleFinding("NOM004", "warning", "Characteristic has no id", ref))
        else:
            seen_ids[c.id] += 1
        if c.nominal is None:
            shown = f" (got {c.raw_nominal!r})" if c.raw_nominal else ""
            out.append(RuleFinding("NOM001", "error", f"Nominal is missing or not numeric{shown}", ref))
        elif c.name:
            by_key[(c.name.strip().lower(), (c.direction or "").upper())].add(c.nominal)

    for id_, n in seen_ids.items():
        if n > 1:
            out.append(RuleFinding("NOM002", "error", f"Characteristic id {id_!r} appears {n} times", id_))
    for (name, direction), noms in by_key.items():
        if len(noms) > 1:
            out.append(
                RuleFinding("NOM003", "warning", f"{name!r} ({direction or 'no direction'}) has conflicting nominals {sorted(noms)}")
            )
    return out
