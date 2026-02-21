from __future__ import annotations

import pytest

from tests._helpers.envelope_assert import assert_is_envelope


@pytest.mark.contract
@pytest.mark.asyncio
async def test_guest_login_sets_cookie_attributes_minimum(client):
    """
    SSOT:
    - HttpOnly / Secure / SameSite=Lax / Path=/
    주의: 테스트 환경에서 Secure가 빠질 수 있으면 이 테스트는 깨질 수 있음.
    """
    url = "/api/v1/auth/guest-login"
    resp = await client.post(url, json={"username": "tester_cookie_attr"})
    assert resp.status_code == 200
    assert_is_envelope(resp.json(), ok=True, meta_is_null=True)

    sc = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in sc
    assert "SameSite=lax" in sc
    assert "Path=/" in sc
    assert "Secure" in sc  # 로컬에서 깨지면 SSOT/환경 정책을 다시 정해야 함
