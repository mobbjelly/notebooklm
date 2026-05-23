from fastapi import APIRouter
from .routes import notebooks, documents, chat, analysis, reports

router = APIRouter()
router.include_router(notebooks.router)
router.include_router(documents.router)
router.include_router(chat.router)
router.include_router(analysis.router)
router.include_router(reports.router)
