from __future__ import annotations

import pytest
from fastapi import status
from httpx import AsyncClient

from app.domain.events import RoomSnapshotType
from app.infra.pubsub.topics import RoomTopic
from app.mvp import MVP_ROOM_ID
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import JoinRoomReason
from app.schemas.room.response import JoinRoomCode, JoinRoomResponse
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import join_room
from tests.realtime.sse.room_actions.conftest import FakeRoomEventBus


@pytest.mark.anyio
async def test_join_room_emits_member_joined_event(
    client: AsyncClient, user_auth: UserAuth, fake_bus: FakeRoomEventBus
) -> None:
    """
    join_room에서 실제로 join이 발생하면, Redis pubsub에는 snapshot이 아니라
    delta event가 publish된다.
    """
    room_id = MVP_ROOM_ID
    r = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert r.status_code == status.HTTP_200_OK, r.text

    envelope = JoinRoomResponse.model_validate(r.json())
    assert envelope.ok is True
    assert envelope.code == JoinRoomCode.OK

    mutation = envelope.data
    assert mutation
    assert mutation.target == Target.ROOM
    assert mutation.subject == Subject.ME
    assert mutation.subject_id is None
    assert mutation.on_target is True
    assert mutation.changed is True
    assert mutation.reason == JoinRoomReason.JOINED

    # 상태 변화가 있었다면 publish 되어야 함
    assert len(fake_bus.calls) == 1
    call = fake_bus.calls[0]
    assert call.topic == RoomTopic(room_id)
    assert call.event.type == RoomSnapshotType.MEMBER_JOINED
    assert call.event.user_id == user_auth["id"]


@pytest.mark.anyio
async def test_join_room_does_not_emit_when_already_joined(
    client: AsyncClient, user_auth: UserAuth, fake_bus: FakeRoomEventBus
) -> None:
    """
    이미 방에 들어가 있는 경우(JoinRoomReason.ALREADY_JOINED)에는 상태 변화가 없으므로
    publish하지 않는다.
    """
    room_id = MVP_ROOM_ID
    # 첫 join: join 발생 -> publish 1회
    _ = await join_room(client, room_id)
    assert len(fake_bus.calls) == 1

    # 두 번째 join: already joined -> publish 증가 없음
    r = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert r.status_code == status.HTTP_200_OK, r.text

    envelope = JoinRoomResponse.model_validate(r.json())
    assert envelope.ok is True
    assert envelope.code == JoinRoomCode.OK

    mutation = envelope.data
    assert mutation
    assert mutation.target == Target.ROOM
    assert mutation.subject == Subject.ME
    assert mutation.subject_id is None
    assert mutation.on_target is True
    assert mutation.changed is False
    assert mutation.reason == JoinRoomReason.ALREADY_JOINED

    assert len(fake_bus.calls) == 1
