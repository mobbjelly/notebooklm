from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, text
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_compatible_schema)


def _ensure_compatible_schema(sync_conn):
    inspector = inspect(sync_conn)
    if "notebooks" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("notebooks")}
    missing_columns = {
        "report_cache": "TEXT",
        "report_status": "VARCHAR(20) DEFAULT 'idle'",
        "report_error": "TEXT",
    }
    for column_name, column_type in missing_columns.items():
        if column_name not in columns:
            sync_conn.execute(text(f"ALTER TABLE notebooks ADD COLUMN {column_name} {column_type}"))
