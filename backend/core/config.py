from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "KnowBase"
    DEBUG: bool = False

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/knowbase.db"

    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma"

    DASHSCOPE_API_KEY: str = ""
    LLM_MODEL: str = "qwen-long"
    EMBEDDING_MODEL: str = "text-embedding-v3"

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 8

    CHAT_DAILY_LIMIT: int = 50

    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
