"""POST /compare: validate a CTF against its JT (PLMXML) file."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import compare_service

router = APIRouter(tags=["compare"])


class CompareRequest(BaseModel):
    ctf_file_id: str
    jtxml_file_id: str


@router.post("")
def compare(body: CompareRequest, db: Session = Depends(get_db)) -> dict:
    return compare_service.compare(db, body.ctf_file_id, body.jtxml_file_id)
