from models.document import Document
from services.summary import generate_notebook_report
from services.text_extraction import extract_document_text


async def create_notebook_report(docs: list[Document]) -> dict:
    report_docs = await _attach_report_excerpts(docs)
    if not report_docs:
        return {"error": "No readable document content available yet"}

    result = await generate_notebook_report(report_docs)
    return {
        "title": result.get("title") or "笔记本报告",
        "executive_summary": result.get("executive_summary") or "",
        "sections": _normalize_sections(result.get("sections") or []),
        "key_takeaways": result.get("key_takeaways") or [],
        "next_steps": result.get("next_steps") or [],
    }


async def _attach_report_excerpts(docs: list[Document]) -> list[Document]:
    report_docs = []
    for doc in docs:
        text = await extract_document_text(doc)
        if text:
            doc._report_excerpt = text[:6000]
        if text or doc.summary_text or doc.key_points or doc.user_notes:
            report_docs.append(doc)
    return report_docs


def _normalize_sections(sections: list[dict]) -> list[dict]:
    normalized = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        normalized.append({
            "heading": section.get("heading") or "未命名章节",
            "content": section.get("content") or "",
        })
    return normalized
