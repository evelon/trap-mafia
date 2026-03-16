from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.room import Room
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import JoinRoomReason, LeaveRoomReason
from app.schemas.room.response import JoinRoomResponse, LeaveRoomResponse
from tests._helpers.auth import UserAuth
from tests._helpers.validators import RespValidator

join_room_validator = RespValidator(JoinRoomResponse)
leave_room_validator = RespValidator(LeaveRoomResponse)


@pytest.mark.api
async def test_api_join_room_returns_envelope_with_mutation(
    client: AsyncClient, db_session: AsyncSession, user_auth: UserAuth, user2_hosted_room: Room
):
    """
    API 계약 테스트(얇게):
    - POST /api/v1/rooms/{room_id}/join
    - 200 + Envelope(ok=True, meta=None)
    - data는 Mutation 형식(target/subject/on_target/changed/reason)
    """
    # 1) user_auth (쿠키/유저 확보)
    # 2) room 준비
    room_id = user2_hosted_room.id

    # 3) join
    resp = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert resp.status_code == 200

    env = join_room_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)

    data = env.data
    assert data is not None
    assert data.target == Target.ROOM
    assert data.subject == Subject.ME
    assert data.subject_id is None
    assert data.on_target is True
    assert isinstance(data.changed, bool)
    assert data.reason in (JoinRoomReason.JOINED, JoinRoomReason.ALREADY_JOINED)


@pytest.mark.api
async def test_api_leave_current_room_returns_envelope_with_mutation(
    client: AsyncClient, user_hosted_room: Room
):
    """
    API 계약 테스트(얇게):
    - POST /api/v1/rooms/current/leave
    - 200 + Envelope(ok=True, meta=None)
    - data는 Mutation 형식(on_target=False, reason=left|already_left)
    """
    # 1) user_auth로 로그인되어 방에 host로 있음.

    # 2) leave
    resp2 = await client.post("/api/v1/rooms/current/leave")
    assert resp2.status_code == 200
    env2 = leave_room_validator.assert_envelope(resp2.json(), ok=True, meta_is_null=True)
    data = env2.data
    assert data is not None
    assert data.target == Target.ROOM
    assert data.subject == Subject.ME
    assert data.subject_id is None
    assert data.on_target is False
    assert isinstance(data.changed, bool)
    assert data.reason in (LeaveRoomReason.LEFT, LeaveRoomReason.ALREADY_LEFT)
