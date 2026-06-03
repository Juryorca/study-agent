from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: str
    course_id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    error_message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


class DocumentList(BaseModel):
    documents: list[DocumentRead]
    total: int
