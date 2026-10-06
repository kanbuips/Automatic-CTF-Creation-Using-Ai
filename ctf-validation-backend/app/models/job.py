"""Validation job + status."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_id, utcnow


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String(16), default=JobStatus.PENDING)
    verdict: Mapped[str | None] = mapped_column(String(16), nullable=True)  # pass | review | fail
    approval_status: Mapped[str] = mapped_column(String(16), default="pending")
    part_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    template_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    jtxml_file_id: Mapped[str] = mapped_column(ForeignKey("uploaded_files.id"))
    ctf_file_id: Mapped[str | None] = mapped_column(ForeignKey("uploaded_files.id"), nullable=True)
    stages: Mapped[dict] = mapped_column(JSON, default=dict)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    findings: Mapped[list["Finding"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan", order_by="Finding.id"
    )
    approvals: Mapped[list["Approval"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan", order_by="Approval.id"
    )
