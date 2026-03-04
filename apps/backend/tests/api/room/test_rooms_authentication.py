from __future__ import annotations

import uuid

import pytest

from app.schemas.common.error import AuthErrorCode
from tests._helpers.entity import create_room
from tests._helpers.envelope_assert import assert_is_envelope


@pytest.mark.api
async def test_join_room_requires_authentication(client, db_session):
    """
    rooms 라우터는 router-level RequireAuthentication이 걸려 있어야 한다.
    access_token 쿠키 없이 join 요청 시 401 + Envelope 응답을 반환해야 한다.
    """
    # room은 미리 하나 만들어 둔다 (인증 실패 전에 라우팅 단계에서 막혀야 함)
    fake_user_id = uuid.uuid4()
    room_id = await create_room(db_session, host_id=fake_user_id)

    resp = await client.post(f"/api/v1/rooms/{room_id}/join")

    assert resp.status_code == 401

    body = resp.json()
    env = assert_is_envelope(body, ok=False, meta_is_null=True)

    # 인증 누락 코드 (프로젝트에서 사용하는 코드명에 맞게 유지)
    assert env["code"] == AuthErrorCode.AUTH_UNAUTHORIZED


@pytest.mark.api
async def test_leave_room_requires_authentication(client):
    """
    access_token 쿠키 없이 leave 요청 시 401 + Envelope 응답을 반환해야 한다.
    """
    resp = await client.post("/api/v1/rooms/current/leave")

    assert resp.status_code == 401

    body = resp.json()
    env = assert_is_envelope(body, ok=False, meta_is_null=True)

    assert env["code"] == AuthErrorCode.AUTH_UNAUTHORIZED
