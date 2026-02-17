import os
from pathlib import Path
from typing import AsyncGenerator

import fakeredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infra.db.session import get_db
from app.infra.redis import get_redis_client
from main import api


@pytest_asyncio.fixture
async def async_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh SQLite database file for each test."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(db_url, echo=False)
    try:
        yield engine
    finally:
        await engine.dispose()
        # Best-effort cleanup (Windows may hold locks briefly).
        try:
            os.remove(db_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            pass


@pytest_asyncio.fixture(autouse=True)
async def prepare_database(async_engine: AsyncEngine):
    """Create/drop tables for each test."""
    # Import Base lazily to avoid import-time side effects.
    from app.models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession bound to the per-test engine."""
    SessionMaker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with SessionMaker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    api.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=api),
        base_url="http://test",
    ) as ac:
        yield ac

    api.dependency_overrides.clear()


@pytest.fixture
def fake_redis():
    fake_redis = fakeredis.aioredis.FakeRedis()

    async def override_get_redis_client():
        yield fake_redis

    api.dependency_overrides[get_redis_client] = override_get_redis_client

    yield fake_redis

    api.dependency_overrides.clear()
