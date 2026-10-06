"""Validation schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ValidateRequest(BaseModel):
    jtxml_file_id: str
    ctf_file_id: str | None = None


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule: str
    severity: str
    source: str
    characteristic_id: str | None
    message: str
    confidence: float | None


class JobOut(BaseModel):
    id: str
    status: str
    verdict: str | None
    approval_status: str
    part_name: str | None
    model_name: str | None
    template_version: str | None
    stages: dict
    counts: dict
    error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_job(cls, job) -> "JobOut":
        return cls(
            id=job.id,
            status=job.status,
            verdict=job.verdict,
            approval_status=job.approval_status,
            part_name=job.part_name,
            model_name=job.model_name,
            template_version=job.template_version,
            stages=job.stages or {},
            counts=(job.report or {}).get("counts", {}),
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class JobDetail(JobOut):
    findings: list[FindingOut]

    @classmethod
    def from_job(cls, job) -> "JobDetail":
        base = JobOut.from_job(job).model_dump()
        return cls(**base, findings=[FindingOut.model_validate(f) for f in job.findings])
