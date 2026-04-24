"""
摘要与笔记生成：文档文本 → LLM → 结构化摘要 + 要点 + 笔记
"""
import json
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import settings
from models.document import Document

SUMMARY_PROMPT = """请对以下文档内容进行分析，并以 JSON 格式输出，包含三个字段：
1. summary: 全文摘要（200字以内）
2. key_points: 核心观点列表（3-5条，每条不超过50字）
3. ai_notes: 结构化笔记，包含 concepts（关键概念）、arguments（重要论点）、data（数据引用）、questions（待深入问题）四个数组

只输出 JSON，不要有其他内容。"""


async def generate_summary_and_notes(doc: Document, db):
    text = await _get_doc_text(doc)
    if not text:
        return

    # 超长文档截断，避免超出上下文限制（qwen-long 支持长文但仍需控制）
    text = text[:30000]

    llm = ChatTongyi(
        model_name=settings.LLM_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )

    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=f"文档内容：\n{text}"),
    ]

    try:
        resp = await llm.ainvoke(messages)
        raw = resp.content.strip()
        # 兼容 markdown 代码块包裹
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        doc.summary_text = parsed.get("summary", "")
        doc.key_points = json.dumps(parsed.get("key_points", []), ensure_ascii=False)
        doc.ai_notes = json.dumps(parsed.get("ai_notes", {}), ensure_ascii=False)
    except Exception:
        doc.summary_text = "摘要生成失败，请重试"


async def generate_notebook_analysis(summaries: list[str]) -> dict:
    ANALYSIS_PROMPT = """你是一个知识分析专家。以下是同一笔记本中多个文档的摘要，请进行跨文档分析，以 JSON 格式输出：
{
  "common_themes": ["共同主题列表"],
  "differences": ["主要差异或矛盾点"],
  "blind_spots": ["知识盲点或待补充方向"],
  "synthesis": "综合见解（100字以内）"
}
只输出 JSON。"""

    llm = ChatTongyi(
        model_name=settings.LLM_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )
    content = "\n\n---\n\n".join(f"文档{i+1}摘要：{s}" for i, s in enumerate(summaries))
    resp = await llm.ainvoke([
        SystemMessage(content=ANALYSIS_PROMPT),
        HumanMessage(content=content),
    ])
    raw = resp.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


async def _get_doc_text(doc: Document) -> str:
    if doc.storage_path:
        from pathlib import Path
        path = Path(doc.storage_path)
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    return ""
