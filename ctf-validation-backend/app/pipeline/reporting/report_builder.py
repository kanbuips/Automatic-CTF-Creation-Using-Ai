"""Merges rule + ML + anomaly results into one report dict."""
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone

from app.pipeline.constants import SEVERITIES
from app.pipeline.parsing.jtxml_parser import ParsedJtxml
from app.pipeline.rules.base import RuleFinding


def compute_verdict(counts: dict) -> str:
    if counts.get("critical") or counts.get("error"):
        return "fail"
    if counts.get("warning"):
        return "review"
    return "pass"


def build_report(meta: dict, parsed: ParsedJtxml, findings: list[RuleFinding]) -> dict:
    counts = {sev: 0 for sev in SEVERITIES}
    counts.update(Counter(f.severity for f in findings))
    counts["total"] = len(findings)
    ordered = sorted(findings, key=lambda f: SEVERITIES.index(f.severity))
    return {
        "job_id": meta.get("job_id", ""),
        "filename": meta.get("filename", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "part_name": parsed.part_name,
        "model_name": parsed.model_name,
        "template_version": parsed.template_version,
        "characteristic_count": len(parsed.characteristics),
        "verdict": compute_verdict(counts),
        "approval_status": "pending",
        "counts": counts,
        "by_source": dict(Counter(f.source for f in findings)),
        "anomalies": sorted({f.characteristic_id for f in findings if f.source == "anomaly" and f.characteristic_id}),
        "findings": [asdict(f) for f in ordered],
    }
