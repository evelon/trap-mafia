from __future__ import annotations

import pytest

from app.schemas.auth.response import UserInfoResponse
from tests._helpers.validators import RespValidator, general_failure_validator

info_resp_validator = RespValidator(UserInfoResponse)


@pytest.mark.contract
async def test_guest_login_validation_error_is_wrapped_in_envelope(client):
    """
    SSOT:
    - FastAPI validation 에러(보통 422)까지도 외부로는 Envelope 형태로 감싼다.

    여기서는 status code를 400/422로 고정하지 않는다.
    (너가 나중에 통일할 수 있고, 통일하면 그때 테스트를 강화하면 됨)
    """
    url = "/api/v1/auth/guest-login"

    # username 길이 3..32 위반(짧음)
    resp = await client.post(url, json={"username": "ab"})
    assert resp.status_code in (400, 422)

    body = resp.json()

    _ = general_failure_validator.assert_envelope(body, ok=False, meta_is_null=True)
