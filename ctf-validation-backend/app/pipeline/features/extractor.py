"""Feature extraction -> pandas DataFrame (one row per characteristic)."""
import pandas as pd

from app.pipeline.constants import DIRECTION_CODES, KNOWN_UNITS, PLACEHOLDER_RE
from app.pipeline.parsing.jtxml_parser import ParsedJtxml

FEATURE_COLUMNS = [
    "nominal",
    "upper_tol",
    "lower_tol",
    "band",
    "band_ratio",
    "asymmetry",
    "desc_len",
    "desc_words",
    "has_placeholder",
    "direction_code",
    "unit_known",
    "missing_nominal",
    "missing_tol",
]


def extract_features(parsed: ParsedJtxml) -> pd.DataFrame:
    rows = []
    for i, c in enumerate(parsed.characteristics):
        missing_tol = c.upper_tol is None or c.lower_tol is None
        upper = c.upper_tol or 0.0
        lower = c.lower_tol or 0.0
        nominal = c.nominal if c.nominal is not None else 0.0
        band = upper - lower
        desc = (c.description or "").strip()
        rows.append(
            {
                "characteristic_id": c.id or f"#{i + 1}",
                "nominal": nominal,
                "upper_tol": upper,
                "lower_tol": lower,
                "band": band,
                "band_ratio": band / abs(nominal) if nominal else 0.0,
                "asymmetry": abs(upper + lower),
                "desc_len": len(desc),
                "desc_words": len(desc.split()),
                "has_placeholder": int(bool(PLACEHOLDER_RE.search(desc))),
                "direction_code": DIRECTION_CODES.get((c.direction or "").strip().upper(), 0),
                "unit_known": int((c.unit or "").strip().lower() in KNOWN_UNITS),
                "missing_nominal": int(c.nominal is None),
                "missing_tol": int(missing_tol),
            }
        )
    return pd.DataFrame(rows, columns=["characteristic_id", *FEATURE_COLUMNS])
