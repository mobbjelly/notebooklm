"""
RAG 问答：向量检索 → 构建 Prompt → 流式调用 LLM
"""
import asyncio
import json
from typing import AsyncGenerator

from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import settings

SYSTEM_PROMPT = """你是一个专业的文档分析助手。请严格基于以下文档内容回答用户问题，不要编造文档中没有的内容。
如果文档中没有相关信息，请直接说明"文档中未提及此内容"。
回答时请引用具体来源文档名称。"""


async def rag_stream(
    question: str,
    notebook_id: int,
    doc_id: int | None = None,
) -> AsyncGenerator[tuple[str, list], None]:

    # 1. 检索相关文档块
    chunks, citations = await asyncio.to_thread(_retrieve, question, notebook_id, doc_id)

    if not chunks:
        yield "文档中未找到相关内容，请尝试换个问法或检查文档是否已解析完成。", []
        return

    # 2. 构建 context
    context = "\n\n---\n\n".join(
        f"[来源：{c['doc_name']}]\n{c['text']}" for c in citations
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"文档内容：\n{context}\n\n用户问题：{question}"),
    ]

    # 3. 流式调用通义千问
    llm = ChatTongyi(
        model_name=settings.LLM_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
        streaming=True,
    )

    first = True
    async for chunk in llm.astream(messages):
        text = chunk.content
        if text:
            yield text, citations if first else []
            first = False


def _retrieve(question: str, notebook_id: int, doc_id: int | None) -> tuple[list[str], list[dict]]:
    embeddings = DashScopeEmbeddings(
        model=settings.EMBEDDING_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )
    collection_name = f"notebook_{notebook_id}"
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(settings.CHROMA_DIR),
    )

    where = {"doc_id": doc_id} if doc_id else {"notebook_id": notebook_id}
    results = vectorstore.similarity_search_with_score(
        question,
        k=settings.RAG_TOP_K,
        filter=where,
    )

    chunks = []
    citations = []
    for doc, score in results:
        chunks.append(doc.page_content)
        citations.append({
            "doc_id": doc.metadata.get("doc_id"),
            "doc_name": doc.metadata.get("doc_name"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "text": doc.page_content[:200],
            "score": round(float(score), 4),
        })
    return chunks, citations
