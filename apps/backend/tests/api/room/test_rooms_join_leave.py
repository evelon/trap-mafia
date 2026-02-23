from __future__ import annotations

import uuid

import pytest

from app.models.room import Room
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import JoinRoomReason, LeaveRoomReason
from tests._helpers.envelope_assert import assert_is_envelope


async def _create_room(db, *, host_id: uuid.UUID) -> uuid.UUID:
    room_id = uuid.uuid4()
    db.add(Room(id=room_id, host_id=host_id))
    await db.commit()
    return room_id


@pytest.mark.api
@pytest.mark.asyncio
async def test_api_join_room_returns_envelope_with_mutation(client, db_session):
    """
    API 계약 테스트(얇게):
    - POST /api/v1/rooms/{room_id}/join
    - 200 + Envelope(ok=True, meta=None)
    - data는 Mutation 형식(target/subject/on_target/changed/reason)
    """
    # 1) guest-login (쿠키/유저 확보)
    login = await client.post("/api/v1/auth/guest-login", json={"username": "api_join_1"})
    assert login.status_code == 200
    env_login = assert_is_envelope(login.json(), ok=True, meta_is_null=True)
    user_id = uuid.UUID(env_login["data"]["id"])

    # 2) room 준비
    room_id = await _create_room(db_session, host_id=user_id)

    # 3) join
    resp = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert resp.status_code == 200

    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)
    data = env["data"]
    assert isinstance(data, dict)

    # Mutation 계약(값은 enum serialize로 string일 수 있으니 string 기준으로 확인)
    assert data["target"] == Target.ROOM.value
    assert data["subject"] == Subject.ME.value
    assert data["subject_id"] is None
    assert data["on_target"] is True
    assert isinstance(data["changed"], bool)
    assert data["reason"] in (
        JoinRoomReason.JOINED.value,
        JoinRoomReason.ALREADY_JOINED.value,
    )


@pytest.mark.api
@pytest.mark.asyncio
async def test_api_leave_current_room_returns_envelope_with_mutation(client, db_session):
    """
    API 계약 테스트(얇게):
    - POST /api/v1/rooms/current/leave
    - 200 + Envelope(ok=True, meta=None)
    - data는 Mutation 형식(on_target=False, reason=left|already_left)
    """
    # 1) guest-login
    login = await client.post("/api/v1/auth/guest-login", json={"username": "api_leave_1"})
    assert login.status_code == 200
    env_login = assert_is_envelope(login.json(), ok=True, meta_is_null=True)
    user_id = uuid.UUID(env_login["data"]["id"])

    # 2) room 준비 + join 먼저 (leave는 current 기준이라 active가 있어야 의미 있음)
    room_id = await _create_room(db_session, host_id=user_id)
    join = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert join.status_code == 200
    assert_is_envelope(join.json(), ok=True, meta_is_null=True)

    # 3) leave
    resp = await client.post("/api/v1/rooms/current/leave")
    assert resp.status_code == 200

    env = assert_is_envelope(resp.json(), ok=True, meta_is_null=True)
    data = env["data"]
    assert isinstance(data, dict)

    assert data["target"] == Target.ROOM.value
    assert data["subject"] == Subject.ME.value
    assert data["subject_id"] is None
    assert data["on_target"] is False
    assert isinstance(data["changed"], bool)
    assert data["reason"] in (
        LeaveRoomReason.LEFT.value,
        LeaveRoomReason.ALREADY_LEFT.value,
    )
