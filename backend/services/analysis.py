from models.document import Document
from services.summary import generate_notebook_analysis


async def analyze_notebook(docs: list[Document]) -> dict:
    summaries = [d.summary_text for d in docs if d.summary_text]
    if not summaries:
        return {"error": "No summaries available yet, please wait for document processing"}
    return await generate_notebook_analysis(summaries)
