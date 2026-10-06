"""Schemas for tolerance-transfer generation."""
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    template_file_id: str  # new CTF-PIS (format to keep)
    source_file_id: str  # previous CTF-PIS (tolerances to take)
    overrides: dict[str, str] = Field(default_factory=dict, description="{template_code: source_code}")


class RowResult(BaseModel):
    code: str
    wording: str | None
    status: str
    manual: bool
    source_codes: list[str]
    old: list[float | None]
    new: list[float | None] | None
    note: str


class GenerateResponse(BaseModel):
    file_id: str
    filename: str
    template_version: str | None
    summary: dict[str, int]
    rows: list[RowResult]
