"""POST /generate (fill a new CTF's tolerances from a previous CTF), GET /generate/{id}/download."""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.generate import GenerateRequest, GenerateResponse, RowResult
from app.services import generation_service

router = APIRouter(tags=["generate"])
XLSM = "application/vnd.ms-excel.sheet.macroEnabled.12"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("", response_model=GenerateResponse, status_code=201)
def generate(body: GenerateRequest, db: Session = Depends(get_db)):
    record, result, version = generation_service.generate(db, body.template_file_id, body.source_file_id, body.overrides)
    return GenerateResponse(
        file_id=record.id,
        filename=record.filename,
        template_version=version,
        summary=result.summary(),
        rows=[RowResult(**{**r, "old": list(r["old"]), "new": list(r["new"]) if r["new"] else None}) for r in result.as_dicts()],
    )


@router.get("/{file_id}/download")
def download(file_id: str, db: Session = Depends(get_db)):
    rec = generation_service.get_generated(db, file_id)
    return FileResponse(rec.path, media_type=XLSM if rec.filename.lower().endswith(".xlsm") else XLSX, filename=rec.filename)
