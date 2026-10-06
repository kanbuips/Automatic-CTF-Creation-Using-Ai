"""Tolerance rules."""
from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding, cid

MAX_BAND_RATIO = 0.5


def check(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    out: list[RuleFinding] = []
    for i, c in enumerate(parsed.characteristics):
        ref = cid(c, i)
        if c.upper_tol is None or c.lower_tol is None:
            out.append(RuleFinding("TOL001", "error", "Upper and/or lower tolerance is missing or not numeric", ref))
            continue
        if c.upper_tol < 0:
            out.append(RuleFinding("TOL002", "error", f"Upper tolerance {c.upper_tol:g} must not be negative", ref))
        if c.lower_tol > 0:
            out.append(RuleFinding("TOL003", "error", f"Lower tolerance {c.lower_tol:g} must not be positive", ref))
        band = c.upper_tol - c.lower_tol
        if band == 0:
            out.append(RuleFinding("TOL004", "error", "Tolerance band has zero width", ref))
            continue
        if c.upper_tol > 0 and c.lower_tol < 0 and abs(c.upper_tol + c.lower_tol) > 1e-9:
            out.append(
                RuleFinding("TOL005", "warning", f"Asymmetric tolerance +{c.upper_tol:g}/{c.lower_tol:g}", ref)
            )
        if c.nominal and band / abs(c.nominal) > MAX_BAND_RATIO:
            out.append(RuleFinding("TOL006", "warning", "Tolerance band exceeds 50% of the nominal value", ref))
    return out
