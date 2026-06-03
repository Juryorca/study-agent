"""Pytest fixtures: async test app with in-memory SQLite, no external deps."""

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["CHROMA_PERSIST_DIR"] = "/tmp/chroma_test"
os.environ["UPLOAD_DIR"] = "/tmp/uploads_test"
os.environ["LLM_API_KEY"] = "sk-test"

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.models.base import Base


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
