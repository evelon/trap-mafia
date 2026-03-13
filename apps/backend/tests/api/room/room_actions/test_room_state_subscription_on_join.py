import pytest
from httpx import AsyncClient

from app.domain.events import RoomEventType
from app.mvp import MVP_ROOM_ID
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import (
    assert_room_snapshot_from_sse,
    join_room,
    skip_on_connect_snapshot,
)


@pytest.mark.anyio
@pytest.mark.timeout(10)
async def test_join_room_emits_second_snapshot_on_sse(
    sse_client: AsyncClient,
    sse_client2: AsyncClient,
    sse_user_auth: UserAuth,
    sse_user_auth2: UserAuth,
) -> None:
    # 테스트 환경 검증
    assert sse_user_auth["id"] != sse_user_auth2["id"]
    room_id = MVP_ROOM_ID

    # user1 먼저 입장
    _ = await join_room(sse_client, room_id)

    # user1이 SSE 구독 시작 / 테스트 본문
    async with skip_on_connect_snapshot(sse_client, room_id) as reader:
        # 2) user2 입장 -> delta publish -> user1 SSE에 두 번째 snapshot 와야 함
        _ = await join_room(sse_client2, room_id)

        payload = await reader.read_one(timeout_s=3.0)
        snapshot = assert_room_snapshot_from_sse(payload)
        assert snapshot
        assert snapshot.room.id == room_id

        assert snapshot.last_event
        assert snapshot.last_event == RoomEventType.MEMBER_JOINED
        assert len(snapshot.logs) == 1
        assert "입장" in snapshot.logs[0]

        assert len(snapshot.members) == 2

        member_ids = {member.user_id for member in snapshot.members}
        assert member_ids == {sse_user_auth["id"], sse_user_auth2["id"]}
