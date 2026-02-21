from __future__ import annotations

import pytest

from tests._helpers.envelope_assert import assert_is_envelope


@pytest.mark.api
def test_me_returns_same_user_after_guest_login(client):
    """
    SSOT:
    - guest-login으로 쿠키 세션이 생기면 /auth/me는 그 유저를 반환한다.
    - meta는 항상 null
    """
    login_url = "/api/v1/auth/guest-login"
    me_url = "/api/v1/auth/me"  # TODO: path 확정되면 여기만 바꾸기

    resp_login = client.post(login_url, json={"username": "tester_me"})
    assert resp_login.status_code == 200
    env_login = assert_is_envelope(resp_login.json(), ok=True, meta_is_null=True)
    user_login = env_login["data"]
    user_id = user_login["id"]

    resp_me = client.get(me_url)
    assert resp_me.status_code == 200
    env_me = assert_is_envelope(resp_me.json(), ok=True, meta_is_null=True)
    user_me = env_me["data"]
    assert user_me["id"] == user_id
    assert user_me["username"] == "tester_me"
