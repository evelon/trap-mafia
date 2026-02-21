from __future__ import annotations

from datetime import timedelta

import jwt  # PyJWT
import pytest

from app.core.config import JwtConfig, get_jwt_config
from tests._helpers.envelope_assert import assert_is_envelope


@pytest.fixture
def jwt_test_cfg(app):
    """
    테스트에서 JWT 설정을 고정한다.
    - issuer/audience/secret이 고정돼야 decode_and_verify가 예측 가능해짐
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


def _encode_access(cfg: JwtConfig, *, sub: str, exp_seconds: int = 60) -> str:
    # decode_and_verify()가 require: exp/iat/sub/typ 를 강제하므로 그에 맞춰 만든다.
    # (iss/aud도 검사하므로 cfg와 일치해야 함)
    import time

    now = int(time.time())
    payload = {
        "iss": cfg.issuer,
        "aud": cfg.audience,
        "sub": sub,
        "iat": now,
        "exp": now + exp_seconds,
        "typ": "access",
    }
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_accepts_valid_access_jwt_in_cookie(client, app, jwt_test_cfg: JwtConfig):
    """
    구현 강제 포인트:
    - /me가 access_token 쿠키의 JWT를 decode_and_verify로 검증해야 통과
    """
    token = _encode_access(jwt_test_cfg, sub="tester_me", exp_seconds=60)
    client.cookies.set("access_token", token)

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200

    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)
    data = env["data"]
    assert isinstance(data, dict)

    # 현재 SSOT에서 me 응답이 username을 포함하므로 최소로만 강제
    assert data.get("username") == "tester_me"


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_invalid_signature(client, app, jwt_test_cfg: JwtConfig):
    """
    구현 강제 포인트:
    - 서명 검증 실패(InvalidTokenError)를 잡아서 401 Envelope로 바꿔야 함
    """
    # 다른 secret으로 서명한 토큰
    bad_cfg = JwtConfig(
        issuer=jwt_test_cfg.issuer,
        audience=jwt_test_cfg.audience,
        access_ttl=jwt_test_cfg.access_ttl,
        refresh_ttl=jwt_test_cfg.refresh_ttl,
        algorithm=jwt_test_cfg.algorithm,
        secret_key="wrong-secret",
        public_key=None,
    )
    bad_token = _encode_access(bad_cfg, sub="tester_me", exp_seconds=60)

    client.cookies.set("access_token", bad_token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert isinstance(env["code"], str) and env["code"]  # code 값은 프로젝트 enum에 맞게 강화 가능


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_expired_token(client, app, jwt_test_cfg: JwtConfig):
    """
    구현 강제 포인트:
    - exp 만료를 거부해야 함
    """
    token = _encode_access(jwt_test_cfg, sub="tester_me", exp_seconds=-10)  # 이미 만료
    client.cookies.set("access_token", token)

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert isinstance(env["code"], str) and env["code"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_token_missing_required_claims(client, app, jwt_test_cfg: JwtConfig):
    """
    구현 강제 포인트:
    - decode_and_verify 옵션(require exp/iat/sub/typ) 때문에 누락 시 거부되어야 함
    """
    import time

    now = int(time.time())
    payload = {
        "iss": jwt_test_cfg.issuer,
        "aud": jwt_test_cfg.audience,
        # "sub" missing
        "iat": now,
        "exp": now + 60,
        "typ": "access",
    }
    token = jwt.encode(payload, jwt_test_cfg.secret_key, algorithm=jwt_test_cfg.algorithm)

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert isinstance(env["code"], str) and env["code"]


@pytest.mark.api
@pytest.mark.asyncio
async def test_me_rejects_refresh_token_used_as_access(client, app, jwt_test_cfg: JwtConfig):
    """
    구현 강제 포인트:
    - typ=refresh 토큰을 access_token 쿠키에 넣으면 거부되어야 함
    - 즉 /me에서 claims['typ'] == 'access'를 확인해야 함
    """
    import time

    now = int(time.time())
    payload = {
        "iss": jwt_test_cfg.issuer,
        "aud": jwt_test_cfg.audience,
        "sub": "tester_me",
        "iat": now,
        "exp": now + 60,
        "typ": "refresh",
        "jti": "abc123",
    }
    token = jwt.encode(payload, jwt_test_cfg.secret_key, algorithm=jwt_test_cfg.algorithm)

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert isinstance(env["code"], str) and env["code"]
