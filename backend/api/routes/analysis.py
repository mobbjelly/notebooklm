import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.deps import get_client_id
from models.notebook import Notebook
from models.document import Document, DocumentStatus
from services.analysis import analyze_notebook

router = APIRouter(prefix="/notebooks/{notebook_id}/analysis", tags=["analysis"])


@router.get("")
async def get_analysis(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)
    if not nb.analysis_cache:
        return {"result": None}
    return {"result": json.loads(nb.analysis_cache)}


@router.post("")
async def trigger_analysis(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)

    docs = await db.execute(
        select(Document).where(Document.notebook_id == notebook_id, Document.status == DocumentStatus.ready)
    )
    ready_docs = docs.scalars().all()

    if len(ready_docs) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 ready documents for analysis")

    result = await analyze_notebook(ready_docs)
    nb.analysis_cache = json.dumps(result, ensure_ascii=False)
    await db.commit()
    return {"result": result}


async def _get_owned(notebook_id: int, client_id: str, db: AsyncSession) -> Notebook:
    nb = await db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.client_id == client_id))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return nb
