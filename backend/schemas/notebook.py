from pydantic import BaseModel
from datetime import datetime


class NotebookCreate(BaseModel):
    name: str
    description: str | None = None


class NotebookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class NotebookOut(BaseModel):
    id: int
    name: str
    description: str | None
    share_token: str | None
    doc_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
