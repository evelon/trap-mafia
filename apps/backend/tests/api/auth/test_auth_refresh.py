from __future__ import annotations

import time
from datetime import timedelta

import jwt
import pytest

from app.core.auth import ACCESS_TOKEN, REFRESH_TOKEN
from app.core.config import JwtConfig, get_jwt_config
from tests._helpers.envelope_assert import assert_is_envelope


def _set_cookie_header(resp) -> str:
    # httpx Response: headers.get("set-cookie")가 여러 Set-Cookie를 합쳐서 줄 수 있음
    return resp.headers.get("set-cookie", "")


@pytest.mark.api
@pytest.mark.asyncio
async def test_refresh_issues_new_access_cookie(client):
    """
    요구사항:
    - refresh_token 쿠키가 유효하면 /auth/refresh는 성공(200)하고
      access_token 쿠키를 Set-Cookie로 내려준다.
    - (선택) refresh rotation을 한다면 refresh_token도 새로 내려줄 수 있다.
      -> 이 테스트는 rotation 유무에 대해 관대하게(둘 다 허용) 작성.
    """
    # 1) guest-login으로 유저/refresh 쿠키 확보
    login = await client.post("/api/v1/auth/guest-login", json={"username": "tester_refresh_ok"})
    assert login.status_code == 200
    assert_is_envelope(login.json(), ok=True, meta_is_null=True)

    assert client.cookies.get(REFRESH_TOKEN) is not None, (
        "guest-login이 refresh_token 쿠키를 줘야 함"
    )

    # 2) refresh 호출
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200

    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)

    sc = _set_cookie_header(resp)
    assert f"{ACCESS_TOKEN}=" in sc, f"refresh는 access_token Set-Cookie를 포함해야 함. got={sc}"

    # rotation 정책은 아직 SSOT로 못 박지 않았으니 optional
    # rotation을 한다면 refresh_token도 포함될 것
    # assert f"{REFRESH_TOKEN}=" in sc


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_refresh_token_used_as_access(client):
    """
    요구사항:
    - refresh 토큰(typ=refresh)을 access_token 쿠키에 넣으면 /me에서 거부(401)해야 함.
    """
    login = await client.post(
        "/api/v1/auth/guest-login", json={"username": "tester_refresh_as_access"}
    )
    assert login.status_code == 200
    assert_is_envelope(login.json(), ok=True, meta_is_null=True)

    refresh = client.cookies.get(REFRESH_TOKEN)
    assert refresh is not None

    # access_token 자리에 refresh 토큰을 꽂아버림
    client.cookies.set(ACCESS_TOKEN, refresh)

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert isinstance(env["code"], str) and env["code"]


@pytest.fixture
def jwt_test_cfg(app):
    """
    refresh 테스트는 토큰을 직접 만들기 때문에,
    서버도 동일한 설정으로 검증하도록 dependency override로 고정한다.
    """
    cfg = JwtConfig(
        issuer="trap-mafia-test",
        audience="trap-mafia-test",
        access_ttl=timedelta(minutes=5),
        refresh_ttl=timedelta(days=7),
        algorithm="HS256",
        secret_key="test-secret",
        public_key=None,
    )
    app.dependency_overrides[get_jwt_config] = lambda: cfg
    yield cfg
    app.dependency_overrides.pop(get_jwt_config, None)


def _mint_refresh(
    cfg: JwtConfig,
    *,
    sub: str,
    exp_offset_sec: int,
    jti: str = "jti-1",
    secret_override: str | None = None,
) -> str:
    now = int(time.time())
    payload = {
        "iss": cfg.issuer,
        "aud": cfg.audience,
        "sub": sub,
        "iat": now,
        "exp": now + exp_offset_sec,
        "typ": "refresh",
        "jti": jti,
    }
    secret = secret_override if secret_override is not None else cfg.secret_key
    return jwt.encode(payload, secret, algorithm=cfg.algorithm)


@pytest.mark.api
@pytest.mark.asyncio
async def test_refresh_rejects_expired_or_invalid_refresh_token(client, jwt_test_cfg: JwtConfig):
    """
    요구사항:
    - exp 지난 refresh_token -> 401
    - 서명 틀린 refresh_token -> 401
    """
    # 0) user를 하나 만들어서 sub(user_id)가 실제 DB에 존재하도록
    login = await client.post("/api/v1/auth/guest-login", json={"username": "tester_refresh_bad"})
    assert login.status_code == 200
    env_login = assert_is_envelope(login.json(), ok=True, meta_is_null=True)
    user_id = str(env_login["data"]["id"])  # UUID -> str

    # A) expired refresh
    expired = _mint_refresh(jwt_test_cfg, sub=user_id, exp_offset_sec=-10, jti="expired-1")
    client.cookies.set(REFRESH_TOKEN, expired)

    resp1 = await client.post("/api/v1/auth/refresh")
    assert resp1.status_code == 401
    env1 = assert_is_envelope(resp1.json(), ok=False, meta_is_null=True)
    assert isinstance(env1["code"], str) and env1["code"]

    # B) invalid signature refresh
    invalid_sig = _mint_refresh(
        jwt_test_cfg, sub=user_id, exp_offset_sec=60, jti="bad-1", secret_override="wrong-secret"
    )
    client.cookies.set(REFRESH_TOKEN, invalid_sig)

    resp2 = await client.post("/api/v1/auth/refresh")
    assert resp2.status_code == 401
    env2 = assert_is_envelope(resp2.json(), ok=False, meta_is_null=True)
    assert isinstance(env2["code"], str) and env2["code"]
