"""POST /upload/jtxml, /upload/ctf."""
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.upload import UploadResponse
from app.services import validation_service

router = APIRouter(tags=["upload"])


async def _upload(kind: str, file: UploadFile, db: Session) -> UploadResponse:
    content = await file.read()
    record = validation_service.save_upload(db, kind, file.filename or "", content)
    return UploadResponse(file_id=record.id, kind=kind, filename=record.filename, size=record.size)


@router.post("/jtxml", response_model=UploadResponse, status_code=201)
async def upload_jtxml(file: UploadFile, db: Session = Depends(get_db)):
    return await _upload("jtxml", file, db)


@router.post("/ctf", response_model=UploadResponse, status_code=201)
async def upload_ctf(file: UploadFile, db: Session = Depends(get_db)):
    return await _upload("ctf", file, db)
