from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.mvp import MVP_ROOM_ID
from app.schemas.room.mutation import JoinRoomReason, LeaveRoomReason
from app.schemas.room.response import JoinRoomResponse, LeaveRoomResponse
from tests._helpers.auth import UserAuth
from tests._helpers.validators import RespValidator

join_room_validator = RespValidator(JoinRoomResponse)
leave_room_validator = RespValidator(LeaveRoomResponse)


@pytest.mark.api
async def test_join_is_idempotent_when_already_joined(client: AsyncClient, user_auth: UserAuth):
    """
    - join 두 번 호출하면 두 번째는 changed=False, reason=ALREADY_JOINED
    """
    # user_auth로 로그인
    # 1st join
    r1 = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert r1.status_code == 200
    env1 = join_room_validator.assert_envelope(r1.json(), ok=True, meta_is_null=True)
    assert env1.data is not None
    assert env1.data.changed is True
    assert env1.data.reason == JoinRoomReason.JOINED

    # 2nd join (idempotent)
    r2 = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert r2.status_code == 200
    env2 = join_room_validator.assert_envelope(r2.json(), ok=True, meta_is_null=True)
    assert env2.data is not None
    assert env2.data.changed is False
    assert env2.data.reason == JoinRoomReason.ALREADY_JOINED


@pytest.mark.api
async def test_leave_is_idempotent_when_not_in_room(client: AsyncClient, user_auth: UserAuth):
    """
    - leave를 연속으로 호출하면:
      - 첫 번째: changed=True, reason=LEFT
      - 두 번째: changed=False, reason=ALREADY_LEFT
    """
    # user_auth로 로그인
    # 먼저 join 해서 나갈 상태 만들기
    rj = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert rj.status_code == 200
    _ = join_room_validator.assert_envelope(rj.json(), ok=True, meta_is_null=True)

    # 1st leave
    r1 = await client.post("/api/v1/rooms/current/leave")
    assert r1.status_code == 200
    env1 = leave_room_validator.assert_envelope(r1.json(), ok=True, meta_is_null=True)
    assert env1.data is not None
    assert env1.data.changed is True
    assert env1.data.reason == LeaveRoomReason.LEFT

    # 2nd leave (idempotent)
    r2 = await client.post("/api/v1/rooms/current/leave")
    assert r2.status_code == 200
    env2 = leave_room_validator.assert_envelope(r2.json(), ok=True, meta_is_null=True)
    assert env2.data is not None
    assert env2.data.changed is False
    assert env2.data.reason == LeaveRoomReason.ALREADY_LEFT
