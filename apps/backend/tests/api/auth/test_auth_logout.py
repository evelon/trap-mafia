from __future__ import annotations

import pytest

from app.core.auth import ACCESS_TOKEN, REFRESH_TOKEN
from tests._helpers.envelope_assert import assert_is_envelope


def _set_cookie_header(resp) -> str:
    return resp.headers.get("set-cookie", "")


@pytest.mark.api
@pytest.mark.asyncio
async def test_logout_clears_access_and_refresh_cookies(client):
    """
    SSOT(현재 Notion):
    - POST /api/v1/auth/logout
    - 200 OK + Envelope(ok=True, code=OK, data=None, meta=None)
    - Side effect: access_token/refresh_token 제거 (Max-Age=0)
    """
    # 1) 로그인해서 쿠키 확보
    login = await client.post("/api/v1/auth/guest-login", json={"username": "tester_logout"})
    assert login.status_code == 200
    assert_is_envelope(login.json(), ok=True, meta_is_null=True)

    assert client.cookies.get(ACCESS_TOKEN) is not None
    assert client.cookies.get(REFRESH_TOKEN) is not None

    # 2) logout
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200

    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)
    assert env["data"] is None

    # 3) Set-Cookie로 만료(삭제) 시키는지 확인
    sc = _set_cookie_header(resp)

    # access_token, refresh_token 각각에 대해 만료 세팅이 들어가야 함
    # httpx/ASGI 환경에선 여러 Set-Cookie가 하나로 합쳐질 수 있어 포함 검사로 체크
    assert f"{ACCESS_TOKEN}=" in sc, f"access_token clear Set-Cookie 누락: {sc}"
    assert "Max-Age=0" in sc, f"cookie clear는 Max-Age=0을 포함해야 함: {sc}"

    assert f"{REFRESH_TOKEN}=" in sc, f"refresh_token clear Set-Cookie 누락: {sc}"
    assert "Max-Age=0" in sc, f"cookie clear는 Max-Age=0을 포함해야 함: {sc}"
