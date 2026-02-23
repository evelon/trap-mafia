import os
from pathlib import Path
from typing import AsyncGenerator

import fakeredis
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.auth import JwtHandler
from app.core.config import JwtConfig, Settings, get_jwt_config, get_settings
from app.infra.db.session import get_db
from app.infra.redis import get_redis_client


@pytest.fixture
def app():
    from main import api

    yield api
    api.dependency_overrides.clear()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    return db_path


@pytest.fixture
def db_url(db_path: Path) -> str:
    """Create a fresh SQLite database file for each test."""
    db_url = f"sqlite+aiosqlite:///{db_path}"
    return db_url


@pytest_asyncio.fixture
async def async_engine(db_path: Path, db_url: str) -> AsyncGenerator[AsyncEngine, None]:
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
async def client(app: FastAPI, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="https://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def fake_redis(app):
    fake_redis = fakeredis.aioredis.FakeRedis()

    async def override_get_redis_client():
        yield fake_redis

    app.dependency_overrides[get_redis_client] = override_get_redis_client

    yield fake_redis

    app.dependency_overrides.clear()


@pytest.fixture
def test_settings(db_url: str) -> Settings:
    """테스트용 Settings 단일 소스(override_settings/jwt_test_handler 공용)."""
    return Settings(
        database_url=db_url,
        redis_url="redis://fake_redis/0",
        jwt_secret="test-secret_qyQPnd7XMy5ECrfz0HHJACbd5IDqliDFfse8CNwFEOl",
    )


@pytest.fixture(autouse=True)
def override_settings(app: FastAPI, test_settings: Settings):
    get_settings.cache_clear()
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def jwt_test_config(test_settings: Settings):
    return get_jwt_config(test_settings)


@pytest.fixture
def jwt_test_handler(jwt_test_config: JwtConfig):
    return JwtHandler(jwt_test_config)
