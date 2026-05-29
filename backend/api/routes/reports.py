import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.database import AsyncSessionLocal, get_db
from core.deps import get_client_id
from models.notebook import Notebook
from models.document import Document, DocumentStatus
from services.report import create_notebook_report

router = APIRouter(prefix="/notebooks/{notebook_id}/report", tags=["reports"])

_running_tasks: dict[tuple[str, int], asyncio.Task] = {}


@router.get("")
async def get_report(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)
    result = json.loads(nb.report_cache) if nb.report_cache else None
    return {
        "status": nb.report_status or "idle",
        "result": result,
        "error": nb.report_error,
    }


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def trigger_report(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)

    if nb.report_status == "generating":
        _ensure_task_running(client_id, notebook_id)
        return _report_response(nb)

    ready_count = await _ready_doc_count(notebook_id, db)
    if ready_count < 1:
        raise HTTPException(status_code=400, detail="Need at least 1 ready document for report")

    nb.report_status = "generating"
    nb.report_error = None
    nb.report_cache = None
    await db.commit()
    await db.refresh(nb)

    _ensure_task_running(client_id, notebook_id)
    return _report_response(nb)


@router.post("/cancel")
async def cancel_report(
    notebook_id: int,
    client_id: str = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    nb = await _get_owned(notebook_id, client_id, db)
    task_key = (client_id, notebook_id)
    task = _running_tasks.get(task_key)
    if task and not task.done():
        task.cancel()

    if nb.report_status == "generating":
        nb.report_status = "idle" if not nb.report_cache else "ready"
        nb.report_error = None
        await db.commit()
        await db.refresh(nb)
    return _report_response(nb)


def _report_response(nb: Notebook) -> dict:
    return {
        "status": nb.report_status or "idle",
        "result": json.loads(nb.report_cache) if nb.report_cache else None,
        "error": nb.report_error,
    }


def _ensure_task_running(client_id: str, notebook_id: int):
    task_key = (client_id, notebook_id)
    if task_key in _running_tasks:
        return
    _running_tasks[task_key] = asyncio.create_task(_run_report_task(client_id, notebook_id, task_key))


def cancel_running_report(client_id: str, notebook_id: int):
    task = _running_tasks.get((client_id, notebook_id))
    if task and not task.done():
        task.cancel()


async def _run_report_task(client_id: str, notebook_id: int, task_key: tuple[str, int]):
    try:
        async with AsyncSessionLocal() as db:
            nb = await _get_owned(notebook_id, client_id, db)
            docs = await db.execute(
                select(Document).where(Document.notebook_id == notebook_id, Document.status == DocumentStatus.ready)
            )
            ready_docs = docs.scalars().all()
            if not ready_docs:
                nb.report_status = "failed"
                nb.report_error = "Need at least 1 ready document for report"
                await db.commit()
                return

            result = await asyncio.wait_for(
                create_notebook_report(ready_docs),
                timeout=settings.REPORT_GENERATION_TIMEOUT_SECONDS,
            )
            if result.get("error"):
                nb.report_status = "failed"
                nb.report_error = result["error"]
                await db.commit()
                return

            nb.report_cache = json.dumps(result, ensure_ascii=False)
            nb.report_status = "ready"
            nb.report_error = None
            await db.commit()
    except asyncio.CancelledError:
        async with AsyncSessionLocal() as db:
            nb = await _get_owned(notebook_id, client_id, db)
            if nb.report_status == "generating":
                nb.report_status = "idle" if not nb.report_cache else "ready"
                nb.report_error = None
                await db.commit()
        raise
    except asyncio.TimeoutError:
        async with AsyncSessionLocal() as db:
            nb = await _get_owned(notebook_id, client_id, db)
            nb.report_status = "failed"
            nb.report_error = f"Report generation timed out after {settings.REPORT_GENERATION_TIMEOUT_SECONDS} seconds"
            await db.commit()
    except Exception as exc:
        async with AsyncSessionLocal() as db:
            nb = await _get_owned(notebook_id, client_id, db)
            nb.report_status = "failed"
            nb.report_error = str(exc)
            await db.commit()
    finally:
        _running_tasks.pop(task_key, None)


async def _ready_doc_count(notebook_id: int, db: AsyncSession) -> int:
    docs = await db.execute(
        select(Document.id).where(Document.notebook_id == notebook_id, Document.status == DocumentStatus.ready)
    )
    return len(docs.scalars().all())


async def _get_owned(notebook_id: int, client_id: str, db: AsyncSession) -> Notebook:
    nb = await db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.client_id == client_id))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return nb
