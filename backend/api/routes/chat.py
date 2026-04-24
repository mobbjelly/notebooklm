import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.database import get_db
from core.deps import get_client_id
from models.notebook import Notebook
from models.chat import ChatMessage
from schemas.chat import ChatRequest, ChatMessageOut
from services.rag import rag_stream

router = APIRouter(prefix="/notebooks/{notebook_id}/chat", tags=["chat"])


@router.get("", response_model=list[ChatMessageOut])
async def get_history(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns(notebook_id, client_id, db)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.notebook_id == notebook_id).order_by(ChatMessage.created_at)
    )
    return [ChatMessageOut.model_validate(m) for m in result.scalars().all()]


@router.post("")
async def chat(
    notebook_id: int,
    body: ChatRequest,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns(notebook_id, client_id, db)

    # 保存用户消息
    user_msg = ChatMessage(notebook_id=notebook_id, role="user", content=body.question)
    db.add(user_msg)
    await db.commit()

    async def event_stream():
        full_answer = ""
        citations = []
        async for chunk, chunk_citations in rag_stream(body.question, notebook_id, body.doc_ids):
            full_answer += chunk
            if chunk_citations:
                citations = chunk_citations
            yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"

        # 保存 assistant 消息
        assistant_msg = ChatMessage(
            notebook_id=notebook_id,
            role="assistant",
            content=full_answer,
            citations=json.dumps(citations, ensure_ascii=False),
        )
        db.add(assistant_msg)
        await db.commit()
        yield f"data: {json.dumps({'done': True, 'citations': citations}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("")
async def clear_history(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns(notebook_id, client_id, db)
    await db.execute(delete(ChatMessage).where(ChatMessage.notebook_id == notebook_id))
    await db.commit()
    return {"ok": True}


async def _assert_owns(notebook_id: int, client_id: str, db: AsyncSession):
    nb = await db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.client_id == client_id))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
