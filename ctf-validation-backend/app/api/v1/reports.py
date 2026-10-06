"""GET /reports/{id}, /reports/{id}/download."""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.report import ReportOut
from app.services import report_service

router = APIRouter(tags=["reports"])


@router.get("/{job_id}", response_model=ReportOut)
def get_report(job_id: str, db: Session = Depends(get_db)):
    return report_service.get_report(db, job_id)


@router.get("/{job_id}/download")
def download_report(job_id: str, format: str = "xlsx", db: Session = Depends(get_db)):
    path, media_type = report_service.export_report(db, job_id, format)
    return FileResponse(path, media_type=media_type, filename=f"qc-report-{job_id}.{format}")
