"""Approval schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class ApprovalIn(BaseModel):
    decision: Literal["approve", "reject"]
    comment: str = ""
    reviewer: str = "anonymous"

    @model_validator(mode="after")
    def _reject_needs_comment(self):
        if self.decision == "reject" and not self.comment.strip():
            raise ValueError("a comment is required when rejecting")
        return self


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    decision: str
    comment: str
    reviewer: str
    created_at: datetime
