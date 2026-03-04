from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.mvp import MVP_ROOM_ID
from app.schemas.room.mutation import JoinRoomReason, LeaveRoomReason
from tests._helpers.auth import UserAuth
from tests._helpers.envelope_assert import assert_is_envelope


@pytest.mark.api
async def test_join_is_idempotent_when_already_joined(client: AsyncClient, user_auth: UserAuth):
    """
    - join 두 번 호출하면 두 번째는 changed=False, reason=ALREADY_JOINED
    """
    # user_auth로 로그인
    # 1st join
    r1 = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert r1.status_code == 200
    e1 = assert_is_envelope(r1.json(), ok=True, meta_is_null=True)
    assert e1["data"]["changed"] is True
    assert e1["data"]["reason"] == JoinRoomReason.JOINED

    # 2nd join (idempotent)
    r2 = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert r2.status_code == 200
    e2 = assert_is_envelope(r2.json(), ok=True, meta_is_null=True)
    assert e2["data"]["changed"] is False
    assert e2["data"]["reason"] == JoinRoomReason.ALREADY_JOINED


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
    assert_is_envelope(rj.json(), ok=True, meta_is_null=True)

    # 1st leave
    r1 = await client.post("/api/v1/rooms/current/leave")
    assert r1.status_code == 200
    e1 = assert_is_envelope(r1.json(), ok=True, meta_is_null=True)
    assert e1["data"]["changed"] is True
    assert e1["data"]["reason"] == LeaveRoomReason.LEFT

    # 2nd leave (idempotent)
    r2 = await client.post("/api/v1/rooms/current/leave")
    assert r2.status_code == 200
    e2 = assert_is_envelope(r2.json(), ok=True, meta_is_null=True)
    assert e2["data"]["changed"] is False
    assert e2["data"]["reason"] == LeaveRoomReason.ALREADY_LEFT
