from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from app.mvp import MVP_ROOM_ID
from app.schemas.common.error import PermissionErrorCode
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import KickUserReason
from app.schemas.room.response import (
    KickUserCode,
    KickUserResponse,
)
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import join_room
from tests.api.room.room_actions.conftest import FakeRoomEventBus


@pytest.mark.anyio
async def test_kick_user_403_not_in_room(
    client: AsyncClient,
    client2: AsyncClient,
    user_auth: UserAuth,
    user_auth2: UserAuth,
    fake_bus: FakeRoomEventBus,
) -> None:
    user_id1 = user_auth["id"]
    user_id2 = user_auth2["id"]
    invalid_id = uuid4()
    r1 = await client.post(f"/api/v1/rooms/current/users/{user_id1}/kick")
    assert r1.status_code == status.HTTP_403_FORBIDDEN

    envelope1 = r1.json()
    assert envelope1["ok"] is False
    assert envelope1["code"] == PermissionErrorCode.PERMISSION_DENIED_NOT_IN_ROOM

    r2 = await client.post(f"/api/v1/rooms/current/users/{user_id2}/kick")

    envelope2 = r2.json()
    assert envelope2["ok"] is False
    assert envelope2["code"] == PermissionErrorCode.PERMISSION_DENIED_NOT_IN_ROOM

    r3 = await client.post(f"/api/v1/rooms/current/users/{invalid_id}/kick")

    envelope3 = r3.json()
    assert envelope3["ok"] is False
    assert envelope3["code"] == PermissionErrorCode.PERMISSION_DENIED_NOT_IN_ROOM


@pytest.mark.anyio
async def test_kick_user_self_emit_event(
    client: AsyncClient,
    user_auth: UserAuth,
    fake_bus: FakeRoomEventBus,
) -> None:
    room_id = MVP_ROOM_ID
    user_id = user_auth["id"]

    _ = await join_room(client, room_id)
    assert len(fake_bus.calls) == 1

    r1 = await client.post(f"/api/v1/rooms/current/users/{user_id}/kick")
    assert r1.status_code == status.HTTP_200_OK

    envelope = KickUserResponse.model_validate(r1.json())
    assert envelope.ok is True
    assert envelope.code == KickUserCode.OK

    mutation = envelope.data
    assert mutation
    assert mutation.target == Target.ROOM
    assert mutation.subject == Subject.USER
    assert mutation.subject_id == user_id
    assert mutation.on_target is False
    assert mutation.changed is True
    assert mutation.reason == KickUserReason.KICKED

    # 상태 변화가 있었다면 publish 되어야 함
    assert len(fake_bus.calls) == 2

    # 다시 kick을 시도하면 not in room 403
    r2 = await client.post(f"/api/v1/rooms/current/users/{user_id}/kick")
    assert r2.status_code == status.HTTP_403_FORBIDDEN

    envelope2 = r2.json()
    assert envelope2["ok"] is False
    assert envelope2["code"] == PermissionErrorCode.PERMISSION_DENIED_NOT_IN_ROOM

    assert len(fake_bus.calls) == 2


@pytest.mark.anyio
async def test_kick_other_user(
    client: AsyncClient,
    user_auth: UserAuth,
    client2: AsyncClient,
    user_auth2: UserAuth,
    fake_bus: FakeRoomEventBus,
) -> None:
    room_id = MVP_ROOM_ID
    user_id2 = user_auth2["id"]

    _ = await join_room(client, room_id)
    _ = await join_room(client2, room_id)

    assert len(fake_bus.calls) == 2

    r1 = await client.post(f"/api/v1/rooms/current/users/{user_id2}/kick")
    assert r1.status_code == status.HTTP_200_OK

    envelope1 = KickUserResponse.model_validate(r1.json())
    assert envelope1.ok is True
    assert envelope1.code == KickUserCode.OK

    mutation1 = envelope1.data
    assert mutation1
    assert mutation1.target == Target.ROOM
    assert mutation1.subject == Subject.USER
    assert mutation1.subject_id == user_id2
    assert mutation1.on_target is False
    assert mutation1.changed is True
    assert mutation1.reason == KickUserReason.KICKED

    assert len(fake_bus.calls) == 3

    r2 = await client.post(f"/api/v1/rooms/current/users/{user_id2}/kick")
    assert r2.status_code == status.HTTP_200_OK

    envelope2 = KickUserResponse.model_validate(r2.json())
    assert envelope2.ok is True
    assert envelope2.code == KickUserCode.OK

    mutation2 = envelope2.data
    assert mutation2
    assert mutation2.target == Target.ROOM
    assert mutation2.subject == Subject.USER
    assert mutation2.subject_id == user_id2
    assert mutation2.on_target is False
    assert mutation2.changed is False
    assert mutation2.reason == KickUserReason.NOT_IN_ROOM

    assert len(fake_bus.calls) == 3
