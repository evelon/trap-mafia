from __future__ import annotations

import pytest

from tests._helpers.envelope_assert import assert_is_envelope, assert_set_cookie_has_tokens


@pytest.mark.api
@pytest.mark.asyncio
async def test_guest_login_same_username_returns_same_user_id_and_sets_cookies(client):
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

    url = "/api/v1/auth/guest-login"

    resp1 = await client.post(url, json={"username": "tester_01"})
    assert resp1.status_code == 200

    env1 = assert_is_envelope(resp1.json(), ok=True, meta_is_null=True)
    data1 = env1["data"]
    assert isinstance(data1, dict), f"data는 dict여야 함. got={type(data1)}"

    user_id_1 = data1.get("id")
    assert isinstance(user_id_1, str) and user_id_1, "data.id(uuid str)가 필요"
    assert data1.get("username") == "tester_01"

    # in_case / current_case_id는 SSOT에 따라 존재해야 함
    assert isinstance(data1.get("in_case"), bool)
    assert (data1.get("current_case_id") is None) or isinstance(data1.get("current_case_id"), str)

    set_cookie_1 = resp1.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_1)

    resp2 = await client.post(url, json={"username": "tester_01"})
    assert resp2.status_code == 200

    env2 = assert_is_envelope(resp2.json(), ok=True, meta_is_null=True)
    data2 = env2["data"]
    user_id_2 = data2.get("id")

    assert user_id_2 == user_id_1, "같은 username이면 같은 user id여야 함"

    set_cookie_2 = resp2.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_2)
