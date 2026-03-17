from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.schemas.auth.response import UserInfoResponse
from tests._helpers.auth import UserAuth, login_url
from tests._helpers.validators import (
    RespValidator,
    assert_set_cookie_has_tokens,
)

info_resp_validator = RespValidator(UserInfoResponse)


@pytest.mark.api
async def test_guest_login_same_username_returns_same_user_id_and_sets_cookies(
    client: AsyncClient, user_auth: UserAuth
):
    """
    SSOT:
    - same username -> same user id
    - sign up / log in 구분 없음
    - 매 요청마다 access/refresh 쿠키 재발급
    - meta는 항상 null
    """
    user_id = str(user_auth["id"])
    username = user_auth["username"]
    resp = user_auth["response"]
    # Set-Cookie 최소 검증(토큰 2개 존재)
    set_cookie_1 = resp.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_1)

    resp2 = await client.post(login_url, json={"username": username})
    assert resp2.status_code == 200

    env2 = info_resp_validator.assert_envelope(resp2.json(), ok=True, meta_is_null=True)
    assert env2.data is not None
    assert str(env2.data.id) == user_id, "같은 username이면 같은 user id여야 함"

    set_cookie_2 = resp2.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_2)
