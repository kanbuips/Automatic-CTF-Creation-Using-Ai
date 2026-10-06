"""Validation business logic: uploads, job creation and pipeline execution."""
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, PayloadTooLargeError, UnprocessableError
from app.db.session import SessionLocal
from app.models import CtfRecord, Finding, Job, JobStatus
from app.pipeline.orchestrator import PipelineError, run_pipeline

log = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    "jtxml": {".jtxml", ".xml", ".plmxml"},
    "ctf": {".xlsx", ".xlsm", ".xls", ".csv"},
}


def save_upload(db: Session, kind: str, filename: str, content: bytes) -> CtfRecord:
    settings = get_settings()
    name = Path(filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS[kind]:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS[kind]))
        raise UnprocessableError(f"Unsupported {kind} file type {suffix or '(none)'}; allowed: {allowed}")
    if not content:
        raise UnprocessableError("Uploaded file is empty")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise PayloadTooLargeError(f"File exceeds {settings.max_upload_mb} MB")

    record = CtfRecord(kind=kind, filename=name, path="", size=len(content))
    db.add(record)
    db.flush()  # assigns the id used as the stored file name
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    path = settings.upload_dir / f"{record.id}{suffix}"
    path.write_bytes(content)
    record.path = str(path)
    db.commit()
    return record


def _get_file(db: Session, file_id: str, kind: str) -> CtfRecord:
    record = db.get(CtfRecord, file_id)
    if record is None or record.kind != kind:
        raise NotFoundError(f"{kind} file {file_id} not found")
    return record


def create_job(db: Session, jtxml_file_id: str, ctf_file_id: str | None) -> Job:
    _get_file(db, jtxml_file_id, "jtxml")
    if ctf_file_id:
        _get_file(db, ctf_file_id, "ctf")
    job = Job(jtxml_file_id=jtxml_file_id, ctf_file_id=ctf_file_id)
    db.add(job)
    db.commit()
    return job


def get_job(db: Session, job_id: str) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")
    return job


def list_jobs(db: Session, limit: int = 100) -> list[Job]:
    return list(db.scalars(select(Job).order_by(Job.created_at.desc()).limit(limit)))


def run_job(job_id: str) -> None:
    """Execute the pipeline for a job (called from the background worker)."""
    settings = get_settings()
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if job is None:
            return
        record = db.get(CtfRecord, job.jtxml_file_id)
        job.status = JobStatus.RUNNING
        db.commit()

        def on_stage(stages: dict) -> None:
            job.stages = stages
            db.commit()

        try:
            result = run_pipeline(
                Path(record.path),
                settings,
                meta={"job_id": job.id, "filename": record.filename},
                on_stage=on_stage,
            )
        except PipelineError as exc:
            job.status, job.error, job.stages = JobStatus.FAILED, str(exc), exc.stages
            db.commit()
            return
        except Exception as exc:  # noqa: BLE001 - never leave a job stuck in "running"
            log.exception("job %s crashed", job_id)
            job.status, job.error = JobStatus.FAILED, str(exc)
            db.commit()
            return

        job.part_name = result.parsed.part_name
        job.model_name = result.parsed.model_name
        job.template_version = result.parsed.template_version
        job.verdict = result.report["verdict"]
        job.report = result.report
        job.stages = result.stages
        job.findings = [
            Finding(
                rule=f.rule,
                severity=f.severity,
                source=f.source,
                characteristic_id=f.characteristic_id,
                message=f.message,
                confidence=f.confidence,
            )
            for f in result.findings
        ]
        job.status = JobStatus.COMPLETED
        db.commit()
