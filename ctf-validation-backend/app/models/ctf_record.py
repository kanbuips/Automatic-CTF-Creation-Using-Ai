"""Uploaded JTXML / CTF file record."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_id, utcnow


class CtfRecord(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(16))  # jtxml | ctf
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(1024))
    size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
