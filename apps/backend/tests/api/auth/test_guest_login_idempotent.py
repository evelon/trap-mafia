from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests._helpers.auth import UserAuth, login_url
from tests._helpers.envelope_assert import assert_is_envelope, assert_set_cookie_has_tokens


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

    NOTE:
    - 이 테스트는 cookie 속성(HttpOnly/Secure/SameSite/Path)을 강제하지 않는다.
      (환경 차이로 깨질 수 있으니, 속성 강제는 별도 contract 테스트로 분리)
    """
    username = user_auth["username"]
    user_id_1 = str(user_auth["id"])
    headers = user_auth["response"].headers
    set_cookie_1 = headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_1)

    resp2 = await client.post(login_url, json={"username": username})
    assert resp2.status_code == 200

    env2 = assert_is_envelope(resp2.json(), ok=True, meta_is_null=True)
    data2 = env2["data"]
    user_id_2 = data2.get("id")

    assert user_id_2 == user_id_1, "같은 username이면 같은 user id여야 함"

    set_cookie_2 = resp2.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_2)
