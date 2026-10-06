"""Report schemas."""
from pydantic import BaseModel


class ReportOut(BaseModel):
    job_id: str
    filename: str
    generated_at: str
    part_name: str | None
    model_name: str | None
    template_version: str | None
    characteristic_count: int
    verdict: str
    approval_status: str
    counts: dict
    by_source: dict
    anomalies: list[str]
    findings: list[dict]
