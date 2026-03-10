from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import JoinRoomReason, LeaveRoomReason
from app.schemas.room.response import JoinRoomResponse, LeaveRoomResponse
from tests._helpers.auth import UserAuth
from tests._helpers.entity import create_room
from tests._helpers.validators import RespValidator

join_room_validator = RespValidator(JoinRoomResponse)
leave_room_validator = RespValidator(LeaveRoomResponse)


@pytest.mark.api
async def test_api_join_room_returns_envelope_with_mutation(
    client: AsyncClient, db_session: AsyncSession, user_auth: UserAuth
):
    """
    API 계약 테스트(얇게):
    - POST /api/v1/rooms/{room_id}/join
    - 200 + Envelope(ok=True, meta=None)
    - data는 Mutation 형식(target/subject/on_target/changed/reason)
    """
    # 1) user_auth (쿠키/유저 확보)
    # 2) room 준비
    room_id = UUID("00000000-0000-0000-0000-000000000000")

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
    client: AsyncClient, db_session: AsyncSession, user_auth: UserAuth
):
    """
    API 계약 테스트(얇게):
    - POST /api/v1/rooms/current/leave
    - 200 + Envelope(ok=True, meta=None)
    - data는 Mutation 형식(on_target=False, reason=left|already_left)
    """
    # 1) user_auth로 로그인
    user_id = user_auth["id"]
    # 2) room 준비 + join 먼저 (leave는 current 기준이라 active가 있어야 의미 있음)
    room_id = await create_room(db_session, host_id=user_id)
    resp1 = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert resp1.status_code == 200
    _ = join_room_validator.assert_envelope(resp1.json(), ok=True, meta_is_null=True)

    # 3) leave
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
