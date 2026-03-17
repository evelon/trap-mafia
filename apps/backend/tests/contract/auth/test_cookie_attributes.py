from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.schemas.auth.response import UserInfoResponse
from tests._helpers.validators import RespValidator

info_resp_validator = RespValidator(UserInfoResponse)


@pytest.mark.contract
async def test_guest_login_sets_cookie_attributes_minimum(client: AsyncClient):
    """
    SSOT:
    - HttpOnly / Secure / SameSite=Lax / Path=/
    주의: 테스트 환경에서 Secure가 빠질 수 있으면 이 테스트는 깨질 수 있음.
    """
    url = "/api/v1/auth/guest-login"
    resp = await client.post(url, json={"username": "tester_cookie_attr"})
    assert resp.status_code == 200
    _ = info_resp_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)

    sc = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in sc
    assert "SameSite=lax" in sc
    assert "Path=/" in sc
    assert "Secure" in sc  # 로컬에서 깨지면 SSOT/환경 정책을 다시 정해야 함
