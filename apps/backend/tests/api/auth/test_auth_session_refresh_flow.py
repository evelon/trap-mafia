from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest

from app.core.config import JwtConfig, get_jwt_config
from tests._helpers.envelope_assert import assert_is_envelope


@pytest.fixture
def jwt_short_access_cfg(app):
    """
    access TTL을 매우 짧게 만들어 '만료 -> refresh -> 복구' 통합 플로우를 안정적으로 테스트한다.
    """
    cfg = JwtConfig(
        issuer="trap-mafia-test",
        audience="trap-mafia-test",
        access_ttl=timedelta(seconds=1),
        refresh_ttl=timedelta(days=7),
        algorithm="HS256",
        secret_key="test-secret",
        public_key=None,
    )
    app.dependency_overrides[get_jwt_config] = lambda: cfg
    yield cfg
    app.dependency_overrides.pop(get_jwt_config, None)


@pytest.mark.api
@pytest.mark.asyncio
async def test_session_flow_expired_access_then_refresh_then_me_ok(client, jwt_short_access_cfg):
    """
    최종 통합 플로우:
    1) guest-login -> access/refresh 쿠키 발급
    2) access 만료
    3) /me -> 401
    4) /refresh -> 200 + 새 access 쿠키
    5) /me -> 200
    """

    # 1) guest-login
    login = await client.post("/api/v1/auth/guest-login", json={"username": "tester_flow"})
    assert login.status_code == 200
    assert_is_envelope(login.json(), ok=True, meta_is_null=True)

    # 2) access 만료 기다리기 (iat/exp가 초 단위라 2초면 안전)
    await asyncio.sleep(2)

    # 3) /me -> 401 (expired access)
    me1 = await client.get("/api/v1/auth/me")
    assert me1.status_code == 401
    env1 = assert_is_envelope(me1.json(), ok=False, meta_is_null=True)
    assert isinstance(env1["code"], str) and env1["code"]

    # 4) /refresh -> 200 + 새 access 쿠키
    ref = await client.post("/api/v1/auth/refresh")
    assert ref.status_code == 200
    assert_is_envelope(ref.json(), ok=True, meta_is_null=True)

    # 5) 다시 /me -> 200
    me2 = await client.get("/api/v1/auth/me")
    assert me2.status_code == 200
    env2 = assert_is_envelope(me2.json(), ok=True, meta_is_null=True)
    assert env2["data"]["username"] == "tester_flow"
