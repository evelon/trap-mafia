from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, AsyncIterator, Awaitable, Callable, Iterator

import fakeredis
import httpx
import pytest
import pytest_asyncio
import redis.asyncio as redis
from fastapi import FastAPI, status
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
from app.infra.pubsub.topics import RoomTopic
from app.infra.pubsub.transport.deps import get_pubsub
from app.infra.redis.client import get_redis_client
from app.models.auth import User
from app.models.room import Room
from app.mvp import create_mvp_lifespan
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.repositories.user import UserRepo
from app.schemas.auth.response import UserInfoResponse
from main import create_app
from tests._helpers.auth import UserAuth, login_url
from tests._helpers.validators import RespValidator


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
async def db_session_(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession bound to the per-test engine."""
    SessionMaker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with SessionMaker() as session:
        yield session


@pytest_asyncio.fixture
async def mvp_app(async_engine: AsyncEngine):
    """Provide an AsyncSession bound to the per-test engine."""
    SessionMaker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    mvp_lifespan = create_mvp_lifespan(SessionMaker)
    app = create_app(lifespan=mvp_lifespan)
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def app(mvp_app):
    yield mvp_app


@pytest_asyncio.fixture
async def client(app: FastAPI, db_session_: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session_

    app.dependency_overrides[get_db] = override_get_db
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="https://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(client, db_session_: AsyncSession) -> AsyncSession:
    return db_session_


@pytest_asyncio.fixture
async def init_lifespan(client):
    return None


@pytest_asyncio.fixture
async def client2(
    client,
    app: FastAPI,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="https://test",
        ) as ac:
            yield ac


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


async def _user_auth(client: AsyncClient, username: str) -> UserAuth:
    resp = await client.post(login_url, json={"username": username})
    assert resp.status_code == 200
    resp_validator = RespValidator(UserInfoResponse)
    env = resp_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)
    assert env.data is not None
    user_id = env.data.id
    cookies = resp.cookies
    access_token = cookies.get(ACCESS_TOKEN)
    refresh_token = cookies.get(REFRESH_TOKEN)
    assert access_token is not None
    assert refresh_token is not None
    return {
        "id": user_id,
        "username": username,
        "envelope": env,
        "cookies": dict(cookies),
        ACCESS_TOKEN: access_token,
        REFRESH_TOKEN: refresh_token,
        "response": resp,
    }


@pytest_asyncio.fixture
async def user_auth(client: AsyncClient) -> UserAuth:
    return await _user_auth(client, "username")


@pytest_asyncio.fixture
async def user_auth2(client2: AsyncClient) -> UserAuth:
    return await _user_auth(client2, "username2")


@pytest.fixture
async def user_repo(db_session: AsyncSession) -> UserRepo:
    user_repo = UserRepo(db_session)
    return user_repo


@pytest.fixture
def room_repo(db_session: AsyncSession) -> RoomRepo:
    room_repo = RoomRepo(db_session)
    return room_repo


@pytest_asyncio.fixture
async def room_member_repo(db_session: AsyncSession) -> RoomMemberRepo:
    room_member_repo = RoomMemberRepo(db_session)
    return room_member_repo


@pytest_asyncio.fixture
async def random_user(db_session: AsyncSession, user_repo: UserRepo) -> User:
    user = await user_repo.create(username="random_user")
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def create_user(
    db_session: AsyncSession, user_repo: UserRepo
) -> Callable[[], Awaitable[User]]:
    counter = 0

    async def create_user_() -> User:
        nonlocal counter
        user = await user_repo.create(username=f"random_user_{counter}")
        await db_session.commit()
        counter += 1
        return user

    return create_user_


@pytest_asyncio.fixture
async def random_room(
    db_session: AsyncSession,
    room_repo: RoomRepo,
    room_member_repo: RoomMemberRepo,
    random_user: User,
) -> Room:
    room = await room_repo.create(host_id=random_user.id, room_name="random_name")
    await room_member_repo.create_membership(user_id=random_user.id, room_id=room.id)
    await db_session.commit()
    return room


@pytest_asyncio.fixture
async def create_room(
    db_session: AsyncSession,
    room_repo: RoomRepo,
    room_member_repo: RoomMemberRepo,
) -> Callable[[User], Awaitable[Room]]:
    counter = 0

    async def create_room_(user: User) -> Room:
        nonlocal counter
        room = await room_repo.create(host_id=user.id, room_name=f"random_room_{counter}")
        await room_member_repo.create_membership(user_id=user.id, room_id=room.id)
        await db_session.commit()
        counter += 1
        return room

    return create_room_


@pytest_asyncio.fixture
async def add_user_to_room(
    db_session: AsyncSession, room_member_repo: RoomMemberRepo
) -> Callable[[Room, User], Awaitable[None]]:
    async def add_user_(room: Room, user: User) -> None:
        await room_member_repo.create_membership(user_id=user.id, room_id=room.id)
        await db_session.commit()

    return add_user_


@pytest_asyncio.fixture
async def add_new_user_to_room(
    create_user: Callable[[], Awaitable[User]],
    add_user_to_room: Callable[[Room, User], Awaitable[None]],
) -> Callable[[Room], Awaitable[User]]:
    async def add_new_user_to_room_(room: Room) -> User:
        user = await create_user()
        await add_user_to_room(room, user)
        return user

    return add_new_user_to_room_


@pytest_asyncio.fixture
async def user_hosted_room(
    db_session: AsyncSession,
    room_repo: RoomRepo,
    room_member_repo: RoomMemberRepo,
    user_auth: UserAuth,
) -> Room:
    host_id = user_auth["id"]
    room = await room_repo.create(host_id=host_id, room_name="random_room")
    _ = await room_member_repo.create_membership(user_id=host_id, room_id=room.id)
    await db_session.commit()
    return room


# @pytest_asyncio.fixture
# async def add_players_to_room(
#     room_member_repo: RoomMemberRepo
# ) -> Callable[[Room, list[User]]]


@pytest_asyncio.fixture
async def user2_hosted_room(
    db_session: AsyncSession,
    room_repo: RoomRepo,
    room_member_repo: RoomMemberRepo,
    user_auth2: UserAuth,
) -> Room:
    host_id = user_auth2["id"]
    room = await room_repo.create(host_id=host_id, room_name="random_room")
    _ = await room_member_repo.create_membership(user_id=host_id, room_id=room.id)
    await db_session.commit()
    return room


@dataclass
class _Published:
    topic: RoomTopic
    message: str


class FakePubSub:
    """
    Minimal fake implementation of the PubSub interface for unit-testing RoomEventBus.

    - publish(topic, message): records messages and enqueues them for subscribe().
    - subscribe(topic): yields enqueued messages for that topic, then completes.
    """

    def __init__(self) -> None:
        self.published: list[_Published] = []
        self._queues: dict[RoomTopic, deque[str]] = defaultdict(deque)

    async def publish(self, topic: RoomTopic, message: str) -> int:
        self.published.append(_Published(topic=topic, message=message))
        self._queues[topic].append(message)
        return 1

    async def subscribe(self, topic: RoomTopic) -> AsyncIterator[str]:
        q = self._queues[topic]
        while q:
            yield q.popleft()


@pytest.fixture
def fake_pubsub(app: FastAPI):
    fake_pubsub = FakePubSub()

    async def override_get_pubsub():
        yield fake_pubsub

    app.dependency_overrides[get_pubsub] = override_get_pubsub

    yield fake_pubsub

    app.dependency_overrides.clear()


###############################################################################
###### realtime fixtures
###############################################################################

info_resp_validator = RespValidator(UserInfoResponse)


# ✅ 여기만 너 프로젝트에 맞게 고치면 됨
UVICORN_APP = "main:api"
HEALTH_PATH = "/api/health"  # 예: "/health" (없으면 아래 주석 참고)


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@dataclass(frozen=True)
class LiveServer:
    base_url: str
    port: int


def _wait_until_ready(base_url: str, *, timeout_s: float = 8.0) -> None:
    deadline = time.time() + timeout_s
    last_err: Exception | None = None

    # 1) HTTP health check (권장)
    while time.time() < deadline:
        try:
            r = httpx.get(base_url + HEALTH_PATH, timeout=0.2)
            if r.status_code == status.HTTP_200_OK:
                return
        except Exception as e:
            last_err = e
            time.sleep(0.05)

    raise RuntimeError(f"Uvicorn did not become ready. last_err={last_err!r}")


@pytest.fixture
def live_db_path(tmp_path_factory) -> Path:
    # session 동안 유지될 tmp dir
    d = tmp_path_factory.mktemp("live_db")
    return d / "live.db"


@pytest.fixture
def live_db_url(live_db_path: Path) -> str:
    return f"sqlite+aiosqlite:///{live_db_path}"


@pytest_asyncio.fixture
async def live_async_engine(
    live_db_path: Path, live_db_url: str
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(live_db_url, echo=False)
    try:
        yield engine
    finally:
        await engine.dispose()
        # Best-effort cleanup (Windows may hold locks briefly).
        try:
            os.remove(live_db_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            pass


@pytest.fixture(autouse=True)
async def prepare_live_db(live_async_engine: AsyncEngine):
    """Create/drop tables for each test."""
    # Import Base lazily to avoid import-time side effects.
    from app.models.base import Base

    async with live_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with live_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def live_redis_url() -> AsyncGenerator[str, None]:
    redis_url = "redis://127.0.0.1:6379/15"  # 테스트 전용 DB 번호 예시
    client: redis.Redis = redis.from_url(redis_url, decode_responses=True)

    await client.flushdb()
    try:
        yield redis_url
    finally:
        await client.flushdb()
        await client.aclose()  # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue]


@pytest.fixture
def live_server(live_db_url: str, live_redis_url: str) -> Iterator[LiveServer]:
    port = _get_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DATABASE_URL"] = live_db_url
    env["REDIS_URL"] = live_redis_url
    # stderr/stdout를 캡처해두면 실패 시 디버깅 쉬움
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            UVICORN_APP,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        env=env,
        stdout=None,
        stderr=None,
        text=True,
    )

    try:
        _wait_until_ready(base_url, timeout_s=10.0)
        yield LiveServer(base_url=base_url, port=port)

    finally:
        # graceful shutdown 시도
        if proc.poll() is None:
            try:
                proc.terminate()  # SIGTERM on unix, TerminateProcess on win
            except Exception:
                pass

        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            # fallback kill
            try:
                proc.kill()
            except Exception:
                pass
            proc.wait(timeout=3.0)

        # 서버가 부팅 실패했을 때 로그를 보여주면 디버깅 쉬움
        if proc.stdout is not None:
            out = proc.stdout.read()
            if out:
                # 너무 길면 잘라서
                print("\n[uvicorn subprocess output]\n" + out[-4000:])


@pytest_asyncio.fixture
async def sse_client(live_server: LiveServer) -> AsyncGenerator[AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=live_server.base_url,
        timeout=None,
        follow_redirects=True,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def sse_client2(live_server: LiveServer) -> AsyncGenerator[AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=live_server.base_url,
        timeout=None,
        follow_redirects=True,
    ) as client:
        yield client


async def _sse_user_auth(sse_client: AsyncClient, username: str) -> UserAuth:
    resp = await sse_client.post(login_url, json={"username": username})
    assert resp.status_code == 200

    env = info_resp_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)
    assert env.data is not None
    user_id = env.data.id

    # 서버가 Set-Cookie로 내려준 값을 '문자열'로 뽑아낸다
    # (resp.cookies는 secure 정책 때문에 http에선 안 들어있을 수 있음)
    set_cookies = resp.headers.get_list("set-cookie")
    assert set_cookies, "login response has no set-cookie headers"

    # 여기서는 간단히 쿠키 jar에 들어간다고 가정하지 않고,
    # 테스트에서 사용할 Cookie 헤더를 직접 만든다.
    # set-cookie 헤더에서 "name=value"만 뽑기:
    cookie_pairs: list[str] = []
    for sc in set_cookies:
        pair = sc.split(";", 1)[0].strip()  # "ACCESS_TOKEN=..."; "REFRESH_TOKEN=..."
        cookie_pairs.append(pair)

    # ✅ httpx client의 cookie jar에 직접 심어둔다 (Secure 무시)
    for pair in cookie_pairs:
        name, value = pair.split("=", 1)
        sse_client.cookies.set(
            name,
            value,
            domain="127.0.0.1",
            path="/",
        )

    # 필요하면 token 값도 추출 (assert용)
    access_token = None
    refresh_token = None
    for p in cookie_pairs:
        if p.startswith(f"{ACCESS_TOKEN}="):
            access_token = p.split("=", 1)[1]
        if p.startswith(f"{REFRESH_TOKEN}="):
            refresh_token = p.split("=", 1)[1]
    assert access_token is not None
    assert refresh_token is not None

    return {
        "id": user_id,
        "username": username,
        "envelope": env,
        "cookies": dict(sse_client.cookies),
        ACCESS_TOKEN: access_token,
        REFRESH_TOKEN: refresh_token,
        "response": resp,
    }


@pytest_asyncio.fixture
async def sse_user_auth(sse_client: AsyncClient):
    return await _sse_user_auth(sse_client, "username")


@pytest_asyncio.fixture
async def sse_user_auth2(sse_client2: AsyncClient):
    return await _sse_user_auth(sse_client2, "username2")


@pytest_asyncio.fixture
async def sse_user_hosted_room(
    db_session: AsyncSession,
    room_repo: RoomRepo,
    room_member_repo: RoomMemberRepo,
    sse_user_auth: UserAuth,
) -> Room:
    host_id = sse_user_auth["id"]
    room = await room_repo.create(host_id=host_id, room_name="random_room")
    _ = await room_member_repo.create_membership(user_id=host_id, room_id=room.id)
    await db_session.commit()
    return room
