import pytest
from fastapi import status
from httpx import AsyncClient

from app.mvp import MVP_ROOM_ID
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import (
    LeaveRoomReason,
)
from app.schemas.room.response import LeaveRoomCode, LeaveRoomResponse
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import join_room
from tests.realtime.sse.room_actions.conftest import FakeRoomEventBus


@pytest.mark.anyio
async def test_leave_room_does_not_publish_before_join_room(
    client: AsyncClient,
    user_auth: UserAuth,
    fake_room_bus: FakeRoomEventBus,
) -> None:
    r = await client.post("/api/v1/rooms/current/leave")
    assert r.status_code == status.HTTP_200_OK

    envelope = LeaveRoomResponse.model_validate(r.json())
    assert envelope.ok is True
    assert envelope.code == LeaveRoomCode.OK

    mutation = envelope.data
    assert mutation
    assert mutation.target == Target.ROOM
    assert mutation.subject == Subject.ME
    assert mutation.subject_id is None
    assert mutation.on_target is False
    assert mutation.changed is False
    assert mutation.reason == LeaveRoomReason.ALREADY_LEFT

    # 상태 변화가 있었다면 publish 되어야 함
    assert len(fake_room_bus.calls) == 0


@pytest.mark.anyio
async def test_leave_room_publishes_member_left_event(
    client: AsyncClient,
    user_auth: UserAuth,
    fake_room_bus: FakeRoomEventBus,
) -> None:
    room_id = MVP_ROOM_ID
    _ = await join_room(client, room_id)
    assert len(fake_room_bus.calls) == 1

    r = await client.post("/api/v1/rooms/current/leave")
    assert r.status_code == status.HTTP_200_OK

    envelope = LeaveRoomResponse.model_validate(r.json())
    assert envelope.ok is True
    assert envelope.code == LeaveRoomCode.OK

    mutation = envelope.data
    assert mutation
    assert mutation.target == Target.ROOM
    assert mutation.subject == Subject.ME
    assert mutation.subject_id is None
    assert mutation.on_target is False
    assert mutation.changed is True
    assert mutation.reason == LeaveRoomReason.LEFT

    # 상태 변화가 있었다면 publish 되어야 함
    assert len(fake_room_bus.calls) == 2
