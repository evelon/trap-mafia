from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.config import JwtConfig, get_jwt_config
from app.schemas.auth.response import UserInfoResponse
from tests._helpers.auth import UserAuth
from tests._helpers.validators import RespValidator, general_failure_validator

info_resp_validator = RespValidator(UserInfoResponse)


@pytest.fixture
def jwt_short_access_cfg(app: FastAPI):
    """
    access TTL을 매우 짧게 만들어 '만료 -> refresh -> 복구' 통합 플로우를 안정적으로 테스트한다.
    """
    cfg = JwtConfig(
        issuer="trap-mafia-test",
        audience="trap-mafia-test",
        access_ttl=timedelta(seconds=1),
        refresh_ttl=timedelta(days=7),
        algorithm="HS256",
        secret_key="valid-test-token3-valid-test-token3-valid-test-token3",
        public_key=None,
    )
    app.dependency_overrides[get_jwt_config] = lambda: cfg
    yield cfg
    app.dependency_overrides.pop(get_jwt_config, None)


@pytest.mark.api
@pytest.mark.timeout(3)
async def test_session_flow_expired_access_then_refresh_then_me_ok(
    client: AsyncClient, jwt_short_access_cfg: JwtConfig, user_auth: UserAuth
):
    """
    최종 통합 플로우:
    1) guest-login -> access/refresh 쿠키 발급
    2) access 만료
    3) /me -> 401
    4) /refresh -> 200 + 새 access 쿠키
    5) /me -> 200
    """
    # 1) user_auth로 login

    # 2) access 만료 기다리기 (iat/exp가 초 단위라 2초면 안전)
    await asyncio.sleep(2)

    # 3) /me -> 401 (expired access)
    me1 = await client.get("/api/v1/auth/me")
    assert me1.status_code == 401
    _ = general_failure_validator.assert_envelope(me1.json(), ok=False, meta_is_null=True)

    # 4) /refresh -> 200 + 새 access 쿠키
    ref = await client.post("/api/v1/auth/refresh")
    assert ref.status_code == 200
    _ = info_resp_validator.assert_envelope(ref.json(), ok=True, meta_is_null=True)

    # 5) 다시 /me -> 200
    me2 = await client.get("/api/v1/auth/me")
    assert me2.status_code == 200
    env2 = info_resp_validator.assert_envelope(me2.json(), ok=True, meta_is_null=True)
    assert env2.data is not None
    assert env2.data.username == user_auth["username"]
