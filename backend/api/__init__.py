from fastapi import APIRouter
from .routes import notebooks, documents, chat, analysis

router = APIRouter()
router.include_router(notebooks.router)
router.include_router(documents.router)
router.include_router(chat.router)
router.include_router(analysis.router)
