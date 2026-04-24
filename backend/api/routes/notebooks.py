import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.deps import get_client_id
from models.notebook import Notebook
from models.document import Document
from schemas.notebook import NotebookCreate, NotebookUpdate, NotebookOut

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.get("", response_model=list[NotebookOut])
async def list_notebooks(
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notebook).where(Notebook.client_id == client_id).order_by(Notebook.updated_at.desc())
    )
    notebooks = result.scalars().all()
    out = []
    for nb in notebooks:
        count = await db.scalar(select(func.count()).where(Document.notebook_id == nb.id))
        item = NotebookOut.model_validate(nb)
        item.doc_count = count or 0
        out.append(item)
    return out


@router.post("", response_model=NotebookOut, status_code=201)
async def create_notebook(
    body: NotebookCreate,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = Notebook(client_id=client_id, name=body.name, description=body.description)
    db.add(nb)
    await db.commit()
    await db.refresh(nb)
    return NotebookOut.model_validate(nb)


@router.patch("/{notebook_id}", response_model=NotebookOut)
async def update_notebook(
    notebook_id: int,
    body: NotebookUpdate,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)
    if body.name is not None:
        nb.name = body.name
    if body.description is not None:
        nb.description = body.description
    await db.commit()
    await db.refresh(nb)
    return NotebookOut.model_validate(nb)


@router.delete("/{notebook_id}", status_code=204)
async def delete_notebook(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)
    await db.delete(nb)
    await db.commit()


@router.post("/{notebook_id}/share", response_model=NotebookOut)
async def generate_share_token(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)
    nb.share_token = secrets.token_urlsafe(24)
    await db.commit()
    await db.refresh(nb)
    return NotebookOut.model_validate(nb)


@router.get("/shared/{share_token}", response_model=NotebookOut)
async def get_shared_notebook(share_token: str, db: AsyncSession = Depends(get_db)):
    nb = await db.scalar(select(Notebook).where(Notebook.share_token == share_token))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return NotebookOut.model_validate(nb)


async def _get_owned(notebook_id: int, client_id: str, db: AsyncSession) -> Notebook:
    nb = await db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.client_id == client_id))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return nb
