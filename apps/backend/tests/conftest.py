import os
from pathlib import Path
from typing import AsyncGenerator
from uuid import UUID

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

from app.core.config import JwtConfig, Settings, get_jwt_config, get_settings
from app.core.security.jwt import ACCESS_TOKEN, REFRESH_TOKEN, JwtHandler
from app.infra.db.session import get_db
from app.infra.redis.client import get_redis_client
from tests._helpers.auth import login_url
from tests._helpers.envelope_assert import assert_is_envelope


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
        jwt_secret="valid-test-token2-valid-test-token2-valid-test-token2",
    )  # type: ignore[reportCallIssue]


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


@pytest_asyncio.fixture
async def user_auth(client: AsyncClient):
    username = "username"
    resp = await client.post(login_url, json={"username": username})
    assert resp.status_code == 200
    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)
    user_id = UUID(env["data"]["id"])
    cookies = resp.cookies
    access_token = cookies.get(ACCESS_TOKEN)
    refresh_token = cookies.get(REFRESH_TOKEN)
    assert access_token is not None
    assert refresh_token is not None
    return {
        "id": user_id,
        "username": username,
        "envelope": env,
        "cookies": cookies,
        ACCESS_TOKEN: access_token,
        REFRESH_TOKEN: refresh_token,
        "response": resp,
    }
