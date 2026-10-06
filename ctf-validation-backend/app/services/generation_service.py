"""Generate a CTF-PIS from a template workbook with tolerances taken from a previous CTF."""
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models import CtfRecord
from app.pipeline.generation.tolerance_transfer import transfer_tolerances
from app.pipeline.parsing.ctf_parser import parse_ctf


def _ctf(db: Session, file_id: str) -> CtfRecord:
    rec = db.get(CtfRecord, file_id)
    if rec is None or rec.kind != "ctf":
        raise NotFoundError(f"ctf file {file_id} not found")
    return rec


def generate(db: Session, template_id: str, source_id: str, overrides: dict[str, str]):
    template, source = _ctf(db, template_id), _ctf(db, source_id)
    settings = get_settings()
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    record = CtfRecord(kind="generated", filename="", path="", size=0)
    db.add(record)
    db.flush()
    suffix = Path(template.filename).suffix or ".xlsm"
    out = settings.report_dir / f"{record.id}{suffix}"
    result = transfer_tolerances(template.path, source.path, out, overrides)
    record.filename = f"{Path(template.filename).stem}_generated{suffix}"
    record.path, record.size = str(out), out.stat().st_size
    db.commit()
    return record, result, parse_ctf(out).front.get("template_version")


def get_generated(db: Session, file_id: str) -> CtfRecord:
    rec = db.get(CtfRecord, file_id)
    if rec is None or rec.kind != "generated":
        raise NotFoundError(f"generated file {file_id} not found")
    return rec
