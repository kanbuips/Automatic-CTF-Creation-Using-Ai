"""Upload schemas."""
from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    kind: str
    filename: str
    size: int
