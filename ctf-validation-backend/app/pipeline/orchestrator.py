"""Runs stages in order, tracks status.

Stages: parsing -> features -> rules -> ml -> anomaly -> report.
parsing/features/rules/report are fatal on error; ml/anomaly are advisory and are recorded as
failed without aborting the run.
"""
import copy
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from app.pipeline.features.extractor import extract_features
from app.pipeline.ml import anomaly, classifier
from app.pipeline.parsing.jtxml_parser import ParsedJtxml, parse_jtxml
from app.pipeline.reporting.report_builder import build_report
from app.pipeline.rules.base import RuleFinding
from app.pipeline.rules.engine import run_rules

log = logging.getLogger(__name__)

STAGES = ["parsing", "features", "rules", "ml", "anomaly", "report"]
ADVISORY = {"ml", "anomaly"}


class PipelineError(Exception):
    def __init__(self, stage: str, cause: Exception, stages: dict):
        super().__init__(f"{stage} stage failed: {cause}")
        self.stage = stage
        self.stages = stages


@dataclass
class PipelineResult:
    parsed: ParsedJtxml
    findings: list[RuleFinding]
    report: dict
    stages: dict = field(default_factory=dict)


def run_pipeline(
    jtxml_path: Path,
    settings,
    meta: dict | None = None,
    on_stage: Callable[[dict], None] | None = None,
) -> PipelineResult:
    meta = meta or {}
    stages = {name: {"status": "pending"} for name in STAGES}
    ctx: dict = {"findings": []}

    def notify():
        if on_stage:
            on_stage(copy.deepcopy(stages))

    def run_parsing():
        ctx["parsed"] = parse_jtxml(jtxml_path)

    def run_features():
        ctx["df"] = extract_features(ctx["parsed"])

    def run_rules_stage():
        ctx["findings"].extend(run_rules(ctx["parsed"], settings))

    def run_ml():
        ctx["findings"].extend(classifier.predict(ctx["df"], settings))

    def run_anomaly():
        ctx["findings"].extend(anomaly.detect(ctx["df"], settings))

    def run_report():
        ctx["report"] = build_report(meta, ctx["parsed"], ctx["findings"])

    runners = {
        "parsing": run_parsing,
        "features": run_features,
        "rules": run_rules_stage,
        "ml": run_ml,
        "anomaly": run_anomaly,
        "report": run_report,
    }

    for name in STAGES:
        stages[name] = {"status": "running"}
        notify()
        start = time.perf_counter()
        try:
            runners[name]()
        except Exception as exc:  # noqa: BLE001 - stage boundary
            log.exception("pipeline stage %s failed", name)
            stages[name] = {"status": "failed", "error": str(exc), "duration_ms": _ms(start)}
            if name in ADVISORY:
                continue
            for later in STAGES[STAGES.index(name) + 1 :]:
                stages[later] = {"status": "skipped"}
            notify()
            raise PipelineError(name, exc, copy.deepcopy(stages)) from exc
        stages[name] = {"status": "done", "duration_ms": _ms(start)}
        notify()

    ctx["report"]["stages"] = copy.deepcopy(stages)
    return PipelineResult(ctx["parsed"], ctx["findings"], ctx["report"], stages)


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
