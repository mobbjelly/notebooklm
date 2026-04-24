from pydantic import BaseModel
from datetime import datetime


class ChatRequest(BaseModel):
    question: str
    doc_ids: list[int] | None = None   # None 或空列表表示查全部文档


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    citations: str | None   # JSON string
    created_at: datetime

    class Config:
        from_attributes = True
