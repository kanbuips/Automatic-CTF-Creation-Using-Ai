"""Approval business logic."""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models import Approval, JobStatus
from app.services.validation_service import get_job

DECISIONS = {"approve": "approved", "reject": "rejected"}


def submit_approval(db: Session, job_id: str, decision: str, comment: str, reviewer: str) -> Approval:
    job = get_job(db, job_id)
    if job.status != JobStatus.COMPLETED:
        raise ConflictError(f"Job is {job.status}; only completed jobs can be reviewed")
    if decision == "approve" and job.verdict == "fail":
        raise ConflictError("A job with a failing verdict cannot be approved; reject it or fix the file")
    approval = Approval(job_id=job.id, decision=DECISIONS[decision], comment=comment.strip(), reviewer=reviewer)
    job.approval_status = approval.decision
    db.add(approval)
    db.commit()
    return approval


def list_approvals(db: Session, job_id: str) -> list[Approval]:
    return list(get_job(db, job_id).approvals)
