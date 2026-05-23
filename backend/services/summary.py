"""
摘要与笔记生成：文档文本 → LLM → 结构化摘要 + 要点 + 笔记
"""
import json
from langchain_core.messages import HumanMessage, SystemMessage

from models.document import Document
from services.llm_utils import invoke_llm_json
from services.text_extraction import extract_document_text

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

    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=f"文档内容：\n{text}"),
    ]

    try:
        parsed = await invoke_llm_json("summary", messages)
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

    content = "\n\n---\n\n".join(f"文档{i+1}摘要：{s}" for i, s in enumerate(summaries))
    return await invoke_llm_json("analysis", [
        SystemMessage(content=ANALYSIS_PROMPT),
        HumanMessage(content=content),
    ])


async def generate_notebook_report(docs: list[Document]) -> dict:
    REPORT_PROMPT = """你是一个严谨的研究型作者。请根据同一笔记本中的多份文档摘要、要点、正文摘录和用户笔记，写一篇结构完整、可直接阅读的中文长篇报告。

整体必须以 JSON 格式输出，但 executive_summary、sections[].content、key_takeaways[]、next_steps[] 的字符串内容必须使用 Markdown 写作格式，尤其是代码必须使用 fenced code block。

输出 JSON 结构如下：
{
  "title": "报告标题",
  "executive_summary": "Markdown 格式执行摘要（300-500字，概括核心问题、材料范围、主要发现和结论）",
  "sections": [
    {"heading": "章节标题", "content": "Markdown 格式章节正文，要求像文章段落一样展开论述"}
  ],
  "key_takeaways": ["Markdown 格式关键结论列表项"],
  "next_steps": ["Markdown 格式后续行动建议列表项"]
}
要求：
1. 必须覆盖输入中的全部文档，不要遗漏来源；不要编造文档中没有的信息。
2. sections 生成 5-8 个章节，每个章节 400-800 字；每个章节至少包含 2 个自然段。
3. 写作方式要像正式文章：有背景铺垫、概念解释、材料对比、论证展开和小结，不要只列提纲。
4. key_takeaways 生成 6-10 条，每条 50-120 字。
5. next_steps 生成 4-8 条，每条说明具体行动和原因。
6. 如果正文包含代码，必须在 Markdown 中使用三反引号 fenced code block，并写明语言，例如：```js。不要把代码揉进普通段落。
7. JSON 字符串中的 Markdown 换行必须使用合法的 JSON 转义换行；不要输出非法反斜杠转义。
8. 只输出 JSON，不要有其他内容。"""

    content = "\n\n---\n\n".join(_format_doc_for_report(doc, i + 1) for i, doc in enumerate(docs))
    return await invoke_llm_json("report", [
        SystemMessage(content=REPORT_PROMPT),
        HumanMessage(content=f"笔记本材料：\n{content}"),
    ])


def _format_doc_for_report(doc: Document, index: int) -> str:
    parts = [f"文档{index}：{doc.name}（类型：{doc.doc_type}）"]
    report_excerpt = getattr(doc, "_report_excerpt", None)
    if report_excerpt:
        parts.append(f"正文摘录：{report_excerpt}")
    if doc.summary_text:
        parts.append(f"摘要：{doc.summary_text}")
    if doc.key_points:
        parts.append(f"要点：{doc.key_points}")
    if doc.user_notes:
        parts.append(f"用户笔记：{doc.user_notes}")
    if len(parts) == 1:
        parts.append("内容：无可用文本")
    return "\n".join(parts)


async def _get_doc_text(doc: Document) -> str:
    return await extract_document_text(doc)
