"""Runs all rules, collects findings."""
from app.pipeline.constants import SEVERITIES
from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules import (
    direction_rules,
    naming_rules,
    nominal_rules,
    template_rules,
    tolerance_rules,
    wording_rules,
)
from app.pipeline.rules.base import RuleFinding

RULE_MODULES = [
    template_rules,
    naming_rules,
    nominal_rules,
    tolerance_rules,
    direction_rules,
    wording_rules,
]


def run_rules(parsed: ParsedJtxml, settings=None) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    for module in RULE_MODULES:
        findings.extend(module.check(parsed, settings))
    findings.sort(key=lambda f: SEVERITIES.index(f.severity))
    return findings
