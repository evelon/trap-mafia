from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Iterator, Literal

import httpx
import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from app.core.security.jwt import ACCESS_TOKEN, REFRESH_TOKEN
from app.schemas.auth.response import UserInfoResponse
from tests._helpers.auth import UserAuth, login_url
from tests._helpers.validators import RespValidator

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


@pytest.fixture(scope="session")
def live_db_path(tmp_path_factory) -> Path:
    # session 동안 유지될 tmp dir
    d = tmp_path_factory.mktemp("live_db")
    return d / "live.db"


@pytest.fixture(scope="session")
def live_db_url(live_db_path: Path) -> str:
    return f"sqlite+aiosqlite:///{live_db_path}"


@pytest_asyncio.fixture(scope="session")
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


@pytest.fixture(scope="session", autouse=True)
async def prepare_live_db(live_async_engine: AsyncEngine):
    """Create/drop tables for each test."""
    # Import Base lazily to avoid import-time side effects.
    from app.models.base import Base

    async with live_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with live_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def live_server(live_db_url: str) -> Iterator[LiveServer]:
    port = _get_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DATABASE_URL"] = live_db_url
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


async def _sse_user_auth(sse_client: AsyncClient) -> UserAuth:
    username: Literal["username"] = "username"
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
    return await _sse_user_auth(sse_client)


@pytest_asyncio.fixture
async def sse_user_auth2(sse_client2: AsyncClient):
    return await _sse_user_auth(sse_client2)
