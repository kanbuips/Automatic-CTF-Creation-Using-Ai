"""POST /approval/{id} (approve / reject), GET /approval/{id} (audit trail)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.approval import ApprovalIn, ApprovalOut
from app.services import approval_service

router = APIRouter(tags=["approval"])


@router.post("/{job_id}", response_model=ApprovalOut, status_code=201)
def submit(job_id: str, body: ApprovalIn, db: Session = Depends(get_db)):
    return approval_service.submit_approval(db, job_id, body.decision, body.comment, body.reviewer)


@router.get("/{job_id}", response_model=list[ApprovalOut])
def history(job_id: str, db: Session = Depends(get_db)):
    return approval_service.list_approvals(db, job_id)
