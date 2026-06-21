"""Shared test fixtures."""
import os
os.environ["ALLOW_NETWORK"] = "false"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.db.models import Base
from api.db import session as db_session
from api.config import get_settings
get_settings.cache_clear()
from main import app


TEST_DB = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    engine = create_async_engine(TEST_DB, echo=False)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    db_session._engine = engine
    db_session._async_session = sm
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
