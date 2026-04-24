from pydantic import BaseModel, HttpUrl
from datetime import datetime
from models.document import DocumentStatus


class DocumentUrlCreate(BaseModel):
    url: HttpUrl
    name: str | None = None


class DocumentNotesUpdate(BaseModel):
    user_notes: str


class DocumentOut(BaseModel):
    id: int
    notebook_id: int
    name: str
    doc_type: str
    status: DocumentStatus
    chunk_count: int
    summary_text: str | None
    key_points: str | None   # JSON string
    ai_notes: str | None     # JSON string
    user_notes: str | None
    error_msg: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
