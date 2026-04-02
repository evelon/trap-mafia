import anyio
import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.error_codes import PermissionErrorCode
from app.domain.events.room import RoomSnapshotType
from app.mvp import MVP_ROOM_ID
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import (
    assert_room_envelope_from_sse,
    assert_room_snapshot_from_sse,
    join_room,
    leave_room,
    skip_on_connect_snapshot,
)
from tests._helpers.validators import room_sse_validator


@pytest.mark.anyio
async def test_leave_room_closes_current_room_sse_subscription(
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
) -> None:
    room_id = MVP_ROOM_ID
    _ = await join_room(sse_client, room_id)

    async with skip_on_connect_snapshot(sse_client, room_id) as reader:
        _ = await leave_room(sse_client)

        with anyio.fail_after(1):
            payload = await reader.read_one(timeout_s=2.0)
            assert payload["event"] == SSEEventType.ROOM_EVENT
            assert payload["id"] is not None

            sse_data = payload["data"]
            assert isinstance(sse_data, dict)
            assert sse_data["ok"] is True
            assert sse_data["code"] == SSEEnvelopeCode.ROOM_LEAVE
            assert sse_data["data"] is None
            assert sse_data["meta"] is None
            with pytest.raises(StopAsyncIteration):
                await reader.read_one(timeout_s=0.5)


@pytest.mark.anyio
async def test_leave_room_emits_snapshot_to_remaining_member(
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
    sse_client2: AsyncClient,
    sse_user_auth2: UserAuth,
) -> None:
    room_id = MVP_ROOM_ID
    subscriber_user_id = sse_user_auth["id"]
    leaving_user_id = sse_user_auth2["id"]

    _ = await join_room(sse_client, room_id)
    _ = await join_room(sse_client2, room_id)

    async with skip_on_connect_snapshot(sse_client, room_id) as reader:
        _ = await leave_room(sse_client2)

        payload = await reader.read_one(timeout_s=2.0)

        snapshot = assert_room_snapshot_from_sse(payload)

        assert snapshot.last_event == RoomSnapshotType.MEMBER_LEFT

        members = snapshot.members
        assert isinstance(members, list)
        assert len(members) == 1
        assert members[0].user_id == subscriber_user_id
        assert all(member.user_id != leaving_user_id for member in members)

        logs = snapshot.logs
        assert isinstance(logs, list)
        assert len(logs) >= 1

        # idempotent leave 자체는 허용되지만, "추가 SSE 이벤트가 없어야 한다"를
        # live stream read timeout 으로 검증하면 transport cancellation 특성 때문에 flaky 하다.
        # 이 부정(assert-negative) 검증은 lower-level publish/bus 테스트로 내린다.
        _ = await leave_room(sse_client2)


@pytest.mark.anyio
async def test_member_left_receives_last_envelope(
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
) -> None:
    room_id = MVP_ROOM_ID

    _ = await join_room(sse_client, room_id)

    async with skip_on_connect_snapshot(sse_client, room_id) as reader:
        _ = await leave_room(sse_client)
        # kick user snapshot
        payload = await reader.read_one(timeout_s=2.0)
        with pytest.raises(StopAsyncIteration):
            _ = await reader.read_one(timeout_s=2.0)

    body = assert_room_envelope_from_sse(payload)
    envelope = room_sse_validator.assert_envelope(body)

    assert envelope.ok is True
    assert envelope.code == SSEEnvelopeCode.ROOM_LEAVE
    assert envelope.message is None
    assert envelope.data is None


@pytest.mark.anyio
async def test_left_member_cannot_subscribe(
    sse_client: AsyncClient, sse_user_auth: UserAuth
) -> None:
    room_id = MVP_ROOM_ID

    _ = await join_room(sse_client, room_id)
    _ = await leave_room(sse_client)

    resp = await sse_client.get("/rt/v1/sse/rooms/current/state")
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    envelope_dict = resp.json()

    assert envelope_dict["ok"] is False
    assert envelope_dict["code"] == PermissionErrorCode.PERMISSION_DENIED_NOT_IN_ROOM
    assert envelope_dict["message"] is None
    assert envelope_dict["data"] is None
