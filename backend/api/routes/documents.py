import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.deps import get_client_id
from core.config import settings
from models.notebook import Notebook
from models.document import Document, DocumentStatus
from schemas.document import DocumentUrlCreate, DocumentNotesUpdate, DocumentOut
from services.ingestion import ingest_document, delete_document_vectors

router = APIRouter(prefix="/notebooks/{notebook_id}/documents", tags=["documents"])

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
}


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns_notebook(notebook_id, client_id, db)
    result = await db.execute(
        select(Document).where(Document.notebook_id == notebook_id).order_by(Document.created_at.desc())
    )
    return [DocumentOut.model_validate(d) for d in result.scalars().all()]


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_file(
    notebook_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns_notebook(notebook_id, client_id, db)

    doc_type = ALLOWED_TYPES.get(file.content_type)
    if not doc_type:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    save_dir = settings.UPLOAD_DIR / str(notebook_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / file.filename
    content = await file.read()
    save_path.write_bytes(content)

    doc = Document(
        notebook_id=notebook_id,
        name=file.filename,
        doc_type=doc_type,
        storage_path=str(save_path),
        status=DocumentStatus.pending,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(ingest_document, doc.id)
    return DocumentOut.model_validate(doc)


@router.post("/url", response_model=DocumentOut, status_code=201)
async def add_url(
    notebook_id: int,
    body: DocumentUrlCreate,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns_notebook(notebook_id, client_id, db)

    name = body.name or str(body.url).split("/")[-1] or "webpage"
    doc = Document(
        notebook_id=notebook_id,
        name=name,
        doc_type="url",
        source_url=str(body.url),
        status=DocumentStatus.pending,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(ingest_document, doc.id)
    return DocumentOut.model_validate(doc)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    notebook_id: int,
    doc_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns_notebook(notebook_id, client_id, db)
    doc = await _get_doc(doc_id, notebook_id, db)
    if doc.storage_path:
        Path(doc.storage_path).unlink(missing_ok=True)
    await asyncio.to_thread(delete_document_vectors, doc.id, doc.notebook_id)
    await db.delete(doc)
    await db.commit()


@router.patch("/{doc_id}/notes", response_model=DocumentOut)
async def update_notes(
    notebook_id: int,
    doc_id: int,
    body: DocumentNotesUpdate,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    await _assert_owns_notebook(notebook_id, client_id, db)
    doc = await _get_doc(doc_id, notebook_id, db)
    doc.user_notes = body.user_notes
    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


async def _assert_owns_notebook(notebook_id: int, client_id: str, db: AsyncSession):
    nb = await db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.client_id == client_id))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")


async def _get_doc(doc_id: int, notebook_id: int, db: AsyncSession) -> Document:
    doc = await db.scalar(select(Document).where(Document.id == doc_id, Document.notebook_id == notebook_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
