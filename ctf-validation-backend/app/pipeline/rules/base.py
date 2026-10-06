"""Finding type shared by rules, ML and anomaly stages."""
from dataclasses import dataclass


@dataclass
class RuleFinding:
    rule: str
    severity: str  # critical | error | warning | info
    message: str
    characteristic_id: str | None = None
    source: str = "rule"  # rule | ml | anomaly
    confidence: float | None = None


def cid(c, index: int) -> str:
    return c.id or f"#{index + 1}"
