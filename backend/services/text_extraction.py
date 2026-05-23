"""Shared document text extraction utilities."""
import re

import httpx
from readability import Document as ReadabilityDoc
from langchain_community.document_loaders import Docx2txtLoader, TextLoader

from models.document import Document


async def extract_document_text(doc: Document) -> str:
    if doc.doc_type == "url":
        return await _fetch_url(doc.source_url)
    if not doc.storage_path:
        return ""
    if doc.doc_type == "pdf":
        return _extract_pdf(doc.storage_path)
    if doc.doc_type == "docx":
        loader = Docx2txtLoader(doc.storage_path)
        return loader.load()[0].page_content
    loader = TextLoader(doc.storage_path, encoding="utf-8")
    return loader.load()[0].page_content


def _extract_pdf(path: str) -> str:
    import fitz  # pymupdf

    parts = []
    with fitz.open(path) as pdf:
        for page in pdf:
            parts.append(page.get_text("text"))
            for table in page.find_tables():
                rows = table.extract()
                if not rows:
                    continue
                header = "| " + " | ".join(str(cell or "") for cell in rows[0]) + " |"
                sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
                body = "\n".join(
                    "| " + " | ".join(str(cell or "") for cell in row) + " |"
                    for row in rows[1:]
                )
                parts.append(f"\n{header}\n{sep}\n{body}\n")
    return "\n".join(parts).strip()


async def _fetch_url(url: str | None) -> str:
    if not url:
        return ""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    doc = ReadabilityDoc(resp.text)
    text = re.sub(r"<[^>]+>", " ", doc.summary())
    return re.sub(r"\s+", " ", text).strip()
