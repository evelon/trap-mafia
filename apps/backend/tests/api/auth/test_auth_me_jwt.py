from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import pytest
from fastapi import FastAPI

from app.core.auth import ACCESS_TOKEN, JwtHandler
from tests._helpers.envelope_assert import assert_is_envelope

# TODO(SSOT): 네 프로젝트에 맞게 정확한 의존성 provider를 import 해서 override 하자.
# 예)
# from app.core.config import JwtConfig
# from app.core.auth import get_jwt_config   # <- 실제 provider 이름에 맞게
# from app.main import app as fastapi_app    # <- app fixture가 있으면 그걸 쓰면 됨


def _mint_access_token(*, secret_key: str, algorithm: str, sub: str, exp_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_accepts_valid_jwt_in_access_cookie(
    client, app: FastAPI, jwt_test_handler: JwtHandler
):
    """
    요구사항(구현을 강제):
    - /me는 access_token 쿠키의 JWT를 디코딩/검증한다.
    - sub 클레임을 요구(require)한다.
    - 유효하면 ok=True로 응답한다.
    """
    # TODO: 의존성 override로 테스트 전용 secret/alg를 고정하자.
    secret_key = "test-secret"
    algorithm = "HS256"

    username = "tester_me"

    resp = await client.post("/api/v1/auth/guest-login", json={"username": username})
    token = resp.cookies[ACCESS_TOKEN]

    # access_token 쿠키로 /me 호출
    client.cookies.set(ACCESS_TOKEN, token)
    resp = await client.get("/api/v1/auth/me")
    print(resp.json())
    assert resp.status_code == 200

    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)
    data = env["data"]
    assert isinstance(data, dict)

    # SSOT에 따라 user schema가 바뀔 수 있으니 최소로만 강제:
    # - username을 sub로 쓰면 이 assert를 살리고
    # - user_id를 DB에서 읽어오도록 바뀌면, id/username 둘 다 맞게 강화하면 됨.
    assert data.get("username") == username


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_missing_access_cookie(client):
    """
    요구사항:
    - access_token 쿠키가 없으면 401 + Envelope(ok=False) + code=AUTH_TOKEN_NOT_INCLUDED
    """
    client.cookies.pop("access_token", None)

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env["code"] == "AUTH_TOKEN_NOT_INCLUDED"


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_expired_jwt(client, app: FastAPI):
    """
    요구사항:
    - exp 만료 토큰이면 401 + Envelope(ok=False)
    """
    secret_key = "test-secret"
    algorithm = "HS256"

    # TODO: 의존성 override(위와 동일)

    token = _mint_access_token(
        secret_key=secret_key,
        algorithm=algorithm,
        sub="tester_me",
        exp_delta=timedelta(seconds=-10),  # 이미 만료
    )

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    # SSOT에서 expired를 별도 code로 둘 수도 있고, AUTH_UNAUTHORIZED로 뭉칠 수도 있음.
    # 일단 최소로 "인증 실패 코드" 범주만 강제.
    assert env["code"] in ("AUTH_UNAUTHORIZED", "AUTH_TOKEN_EXPIRED")


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_token_with_invalid_signature(client, app: FastAPI):
    """
    요구사항:
    - 서명이 검증되지 않으면 401 + Envelope(ok=False)
    """
    good_secret = "test-secret"
    bad_secret = "bad-secret"
    algorithm = "HS256"

    # TODO: 의존성 override로 good_secret을 서버가 사용하도록 고정

    token = _mint_access_token(
        secret_key=bad_secret,  # 서버 secret과 다르게 서명
        algorithm=algorithm,
        sub="tester_me",
        exp_delta=timedelta(minutes=5),
    )

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env["code"] == "AUTH_UNAUTHORIZED"


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_token_missing_sub(client, app: FastAPI):
    """
    요구사항:
    - sub 클레임이 없으면 401 + Envelope(ok=False)
    - jwt.decode 옵션에서 require=["sub"] 같은 강제를 하게 만드는 테스트
    """
    secret_key = "test-secret"
    algorithm = "HS256"

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            # sub intentionally missing
        },
        secret_key,
        algorithm=algorithm,
    )

    # TODO: 의존성 override로 secret/alg 고정

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env["code"] == "AUTH_UNAUTHORIZED"
