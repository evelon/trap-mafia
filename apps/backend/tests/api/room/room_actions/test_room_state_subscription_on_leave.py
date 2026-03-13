import anyio
import pytest
from httpx import AsyncClient

from app.domain.events import RoomSnapshotType
from app.mvp import MVP_ROOM_ID
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import (
    assert_room_snapshot_from_sse,
    join_room,
    leave_room,
    skip_on_connect_snapshot,
)


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

        with anyio.fail_after(1):
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
