from __future__ import annotations

import pytest

from tests._helpers.envelope_assert import assert_is_envelope, assert_set_cookie_has_tokens


@pytest.mark.api
def test_guest_login_same_username_returns_same_user_id_and_sets_cookies(client):
    """
    SSOT:
    - same username -> same user id
    - sign up / log in 구분 없음
    - 매 요청마다 access/refresh 쿠키 재발급
    - meta는 항상 null
    """
    url = "/api/v1/auth/guest-login"

    resp1 = client.post(url, json={"username": "tester_01"})
    assert resp1.status_code == 200

    body1 = assert_is_envelope(resp1.json(), ok=True, meta_is_null=True)
    data1 = body1["data"]
    assert isinstance(data1, dict), f"data는 dict여야 함. got={type(data1)}"
    assert isinstance(data1.get("id"), str) and data1["id"], "data.id(uuid)가 필요"
    assert data1.get("username") == "tester_01"
    assert isinstance(data1.get("in_case"), bool)
    # current_case_id: uuid|null
    assert (data1.get("current_case_id") is None) or isinstance(data1.get("current_case_id"), str)

    # Set-Cookie 최소 검증(토큰 2개 존재)
    set_cookie_1 = resp1.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_1)

    resp2 = client.post(url, json={"username": "tester_01"})
    assert resp2.status_code == 200

    body2 = assert_is_envelope(resp2.json(), ok=True, meta_is_null=True)
    data2 = body2["data"]
    assert data2["id"] == data1["id"], "같은 username이면 같은 user id여야 함"

    set_cookie_2 = resp2.headers.get("set-cookie", "")
    assert_set_cookie_has_tokens(set_cookie_2)
