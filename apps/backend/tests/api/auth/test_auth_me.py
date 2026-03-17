from __future__ import annotations

import jwt  # PyJWT
import pytest

from app.core.config import JwtConfig
from app.core.security.jwt import ACCESS_TOKEN, JwtHandler
from app.schemas.auth.response import UserInfoResponse
from app.services.auth import AuthService
from tests._helpers.validators import RespValidator, general_failure_validator

info_resp_validator = RespValidator(UserInfoResponse)


def _encode_access(jwt_handler: JwtHandler, *, sub: str, exp_seconds: int = 60) -> str:
    """테스트용 access 토큰을 직접 만든다.

    JwtHandler.decode_and_verify()는 iss/aud 검증 + require(exp/iat/sub/typ)를 강제하므로
    cfg와 일치하는 payload를 만들어 HS256로 서명한다.
    """
    import time

    cfg = jwt_handler.cfg
    now = int(time.time())
    payload: dict[str, object] = {
        "iss": cfg.issuer,
        "aud": cfg.audience,
        "sub": sub,
        "iat": now,
        "exp": now + exp_seconds,
        "typ": "access",
    }
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)


@pytest.mark.api
async def test_me_accepts_valid_access_jwt_in_cookie(
    client, auth_service: AuthService, jwt_test_handler: JwtHandler
):
    """
    구현 강제 포인트:
    - /me가 access_token 쿠키의 JWT를 decode_and_verify로 검증해야 통과
    """
    username = "tester_me"
    user = await auth_service.get_or_create_guest_user(username)
    token = _encode_access(jwt_test_handler, sub=str(user.id), exp_seconds=60)
    client.cookies.set(ACCESS_TOKEN, token)

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200

    env = info_resp_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)
    data = env.data

    # 현재 SSOT에서 me 응답이 username을 포함하므로 최소로만 강제
    assert data is not None
    assert data.username == username


@pytest.mark.api
async def test_me_rejects_invalid_signature(
    client, app, jwt_test_config: JwtConfig, jwt_test_handler: JwtHandler
):
    """
    구현 강제 포인트:
    - 서명 검증 실패(InvalidTokenError)를 잡아서 401 Envelope로 바꿔야 함
    """
    # 다른 secret으로 서명한 토큰
    bad_cfg = JwtConfig(
        issuer=jwt_test_config.issuer,
        audience=jwt_test_config.audience,
        access_ttl=jwt_test_config.access_ttl,
        refresh_ttl=jwt_test_config.refresh_ttl,
        algorithm=jwt_test_config.algorithm,
        secret_key="wrong-test-token-wrong-test-token-wrong-test-token",
        public_key=None,
    )
    bad_handler = JwtHandler(bad_cfg)
    bad_token = _encode_access(bad_handler, sub="tester_me", exp_seconds=60)

    client.cookies.set("access_token", bad_token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    _ = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)


@pytest.mark.api
async def test_me_rejects_expired_token(client, app, jwt_test_handler: JwtHandler):
    """
    구현 강제 포인트:
    - exp 만료를 거부해야 함
    """
    token = _encode_access(jwt_test_handler, sub="tester_me", exp_seconds=-10)  # 이미 만료
    client.cookies.set("access_token", token)

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    _ = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)


@pytest.mark.api
async def test_me_rejects_token_missing_required_claims(client, app, jwt_test_config: JwtConfig):
    """
    구현 강제 포인트:
    - decode_and_verify 옵션(require exp/iat/sub/typ) 때문에 누락 시 거부되어야 함
    """
    import time

    now = int(time.time())
    base_payload = {
        "iss": jwt_test_config.issuer,
        "aud": jwt_test_config.audience,
        "sub": "tester_me",
        "iat": now,
        "exp": now + 60,
        "typ": "access",
    }

    # 1) sub 누락
    payload = dict(base_payload)
    payload.pop("sub", None)
    token = jwt.encode(payload, jwt_test_config.secret_key, algorithm=jwt_test_config.algorithm)

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    _ = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)


@pytest.mark.api
async def test_me_rejects_refresh_token_used_as_access(client, app, jwt_test_config: JwtConfig):
    """
    구현 강제 포인트:
    - typ=refresh 토큰을 access_token 쿠키에 넣으면 거부되어야 함
    - 즉 /me에서 claims['typ'] == 'access'를 확인해야 함
    """
    import time

    now = int(time.time())
    payload = {
        "iss": jwt_test_config.issuer,
        "aud": jwt_test_config.audience,
        "sub": "tester_me",
        "iat": now,
        "exp": now + 60,
        "typ": "refresh",
        "jti": "abc123",
    }
    token = jwt.encode(payload, jwt_test_config.secret_key, algorithm=jwt_test_config.algorithm)

    client.cookies.set("access_token", token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    _ = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)
