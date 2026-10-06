"""Background jobs. Uses FastAPI BackgroundTasks; swap for Celery/RQ by wrapping run_job."""
from app.services.validation_service import run_job


def run_validation_job(job_id: str) -> None:
    run_job(job_id)
