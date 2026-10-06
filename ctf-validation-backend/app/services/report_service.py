"""Report business logic."""
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnprocessableError
from app.models import JobStatus
from app.pipeline.reporting import exporters
from app.services.validation_service import get_job

EXPORTERS = {"xlsx": exporters.to_xlsx, "pdf": exporters.to_pdf}
MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def get_report(db: Session, job_id: str) -> dict:
    job = get_job(db, job_id)
    if job.status != JobStatus.COMPLETED or not job.report:
        raise ConflictError(f"Report not available: job is {job.status}")
    return {**job.report, "approval_status": job.approval_status}


def export_report(db: Session, job_id: str, fmt: str) -> tuple[Path, str]:
    if fmt not in EXPORTERS:
        raise UnprocessableError(f"Unsupported format {fmt!r}; use one of {', '.join(EXPORTERS)}")
    report = get_report(db, job_id)
    report_dir = get_settings().report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    path = EXPORTERS[fmt](report, report_dir / f"{job_id}.{fmt}")  # regenerated: approval status may change
    return path, MEDIA_TYPES[fmt]
