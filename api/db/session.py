"""Async database session factory."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import Base


_engine = None
_async_session = None


def init_db(database_url: str):
    global _engine, _async_session
    _engine = create_async_engine(database_url, echo=False)
    _async_session = async_sessionmaker(_engine, expire_on_commit=False)


async def create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with _async_session() as session:
        yield session
