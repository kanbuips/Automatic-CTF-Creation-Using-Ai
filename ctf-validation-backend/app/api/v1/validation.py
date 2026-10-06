"""POST /validate, GET /validate, GET /validate/{job_id}."""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.validation import JobDetail, JobOut, ValidateRequest
from app.services import validation_service
from app.workers.tasks import run_validation_job

router = APIRouter(tags=["validation"])


@router.post("", response_model=JobOut, status_code=202)
def start_validation(body: ValidateRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    job = validation_service.create_job(db, body.jtxml_file_id, body.ctf_file_id)
    background.add_task(run_validation_job, job.id)
    return JobOut.from_job(job)


@router.get("", response_model=list[JobOut])
def list_jobs(limit: int = 100, db: Session = Depends(get_db)):
    return [JobOut.from_job(j) for j in validation_service.list_jobs(db, min(max(limit, 1), 500))]


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: str, db: Session = Depends(get_db)):
    return JobDetail.from_job(validation_service.get_job(db, job_id))
