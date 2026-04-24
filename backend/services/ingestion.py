"""
文档摄入流水线：解析文本 → 分块 → Embedding → 存入 ChromaDB → 生成摘要笔记
"""
import json
import asyncio
from pathlib import Path

import httpx
from readability import Document as ReadabilityDoc
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

from core.config import settings
from core.database import AsyncSessionLocal
from models.document import Document, DocumentStatus
from services.summary import generate_summary_and_notes


async def ingest_document(doc_id: int):
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if not doc:
            return

        try:
            doc.status = DocumentStatus.processing
            await db.commit()

            text = await _extract_text(doc)
            chunks = _split_text(text)
            await _store_vectors(chunks, doc)

            doc.chunk_count = len(chunks)
            doc.status = DocumentStatus.ready
            await db.commit()

            # 异步触发摘要生成（不阻塞摄入状态更新）
            asyncio.create_task(_run_summary(doc_id))

        except Exception as e:
            doc.status = DocumentStatus.failed
            doc.error_msg = str(e)
            await db.commit()


async def _run_summary(doc_id: int):
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if doc:
            await generate_summary_and_notes(doc, db)
            await db.commit()


async def _extract_text(doc: Document) -> str:
    if doc.doc_type == "url":
        return await _fetch_url(doc.source_url)
    path = doc.storage_path
    if doc.doc_type == "pdf":
        loader = PyPDFLoader(path)
        pages = loader.load()
        return "\n".join(p.page_content for p in pages)
    if doc.doc_type == "docx":
        loader = Docx2txtLoader(path)
        return loader.load()[0].page_content
    # txt / md
    loader = TextLoader(path, encoding="utf-8")
    return loader.load()[0].page_content


async def _fetch_url(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    doc = ReadabilityDoc(resp.text)
    # readability 返回 HTML，简单去标签
    import re
    text = re.sub(r"<[^>]+>", " ", doc.summary())
    return re.sub(r"\s+", " ", text).strip()


def _split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", ".", " "],
    )
    return splitter.split_text(text)


async def _store_vectors(chunks: list[str], doc: Document):
    embeddings = DashScopeEmbeddings(
        model=settings.EMBEDDING_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )
    metadatas = [
        {"doc_id": doc.id, "notebook_id": doc.notebook_id, "doc_name": doc.name, "chunk_index": i}
        for i, _ in enumerate(chunks)
    ]
    collection_name = f"notebook_{doc.notebook_id}"
    await asyncio.to_thread(
        Chroma.from_texts,
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=collection_name,
        persist_directory=str(settings.CHROMA_DIR),
    )


def delete_document_vectors(doc_id: int, notebook_id: int):
    collection_name = f"notebook_{notebook_id}"
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=None,
        persist_directory=str(settings.CHROMA_DIR),
    )
    results = vectorstore.get(where={"doc_id": doc_id})
    ids = results.get("ids", [])
    if ids:
        vectorstore.delete(ids=ids)
