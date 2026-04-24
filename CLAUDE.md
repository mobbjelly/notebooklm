# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KnowBase** — a full-stack personal knowledge management web app (open-source NotebookLM alternative). Users upload documents; AI handles Q&A, summarization, and cross-document analysis. Backend is Python/FastAPI; frontend is React/TypeScript.

## Development Commands

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in DASHSCOPE_API_KEY
uvicorn main:app --reload  # runs on port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Vite dev server on port 3000 (proxies /api/* → localhost:8000)
npm run build    # TypeScript check + production bundle
```

No test suite or linter is configured for either side.

## Required Configuration

Backend needs `backend/.env` with at minimum:

```
DASHSCOPE_API_KEY=your_key_here
```

Optional tuning: `LLM_MODEL`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RAG_TOP_K`, `CHAT_DAILY_LIMIT`.

Runtime data directories (`backend/data/uploads/`, `backend/data/chroma/`, `backend/data/knowbase.db`) are auto-created on startup.

## Architecture

### Backend (`backend/`)

- **`main.py`** — FastAPI app init, CORS (`localhost:3000` hardcoded), DB startup, router mount
- **`core/`** — config (pydantic-settings reading `.env`), async SQLAlchemy engine/session, FastAPI deps
- **`models/`** — SQLAlchemy ORM: `Notebook`, `Document` (status: pending/processing/ready/failed), `ChatMessage`
- **`schemas/`** — Pydantic v2 request/response models
- **`api/routes/`** — route handlers: notebooks CRUD, document upload/URL-add/delete, SSE chat, analysis
- **`services/`** — business logic:
  - `ingestion.py`: parse → chunk → embed → ChromaDB → trigger summary (runs as background `asyncio.create_task`)
  - `rag.py`: vector search → prompt → stream LLM response
  - `summary.py`: auto-generates structured summary+notes after ingestion
  - `analysis.py`: cross-document theme/diff/blind-spot analysis

**LLM/Embeddings**: Alibaba Cloud DashScope (`qwen-long` model, `text-embedding-v3` embeddings) via LangChain wrappers. ChromaDB is the vector store.

**Auth**: Anonymous; client UUID generated in browser localStorage, sent as `X-Client-ID` header.

**DB**: SQLite via aiosqlite/SQLAlchemy async. No migration tooling — schema is `create_all` on startup.

### Frontend (`frontend/src/`)

- **`App.tsx`** — BrowserRouter with two routes: `/` (home) and `/notebook/:id`
- **`pages/`** — `HomePage` (notebook list/create), `NotebookPage` (3-panel layout)
- **`components/`** — `DocumentPanel` (upload/manage/select docs), `ChatPanel` (SSE streaming chat), `AnalysisPanel` (cross-doc results)
- **`store/useAppStore.ts`** — Zustand store holding notebooks, documents, messages, and `streamingText`
- **`api/client.ts`** — all API calls + `chatStream` SSE function using native `ReadableStream`; all TypeScript API types live here

**Vite proxy**: In development, `/api/*` is forwarded to `localhost:8000` — no CORS setup needed in dev.

## Key Constraints

- Changing the frontend port requires updating `allow_origins` in `backend/main.py`.
- The two runtimes must be started independently; there is no unified start script.
- Document ingestion is fire-and-forget (`asyncio.create_task`) — status polling is done by the frontend against the documents endpoint.
