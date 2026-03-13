from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import status
from httpx import AsyncClient, Response

from app.domain.events import RoomSnapshotType
from app.schemas.common.ids import RoomId
from app.schemas.room.state import RoomSnapshot
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType
from tests._helpers.sse import SSEPayload, SSEReader
from tests._helpers.validators import room_sse_validator


async def join_room(client: AsyncClient, room_id: RoomId) -> Response:
    """
    테스트 상황을 만들기 위하여 join_room을 호출한다.
    join_room api 자체는 별도의 테스트로 검증되어야 한다.
    이 함수 내부에서는 최소한의 validation만 진행한다.
    """
    # ✅ TODO: 명세에 따라 body가 필요 없으면 json=None 제거
    resp = await client.post(f"/api/v1/rooms/{room_id}/join")
    assert resp.status_code == status.HTTP_200_OK, resp.text

    body = resp.json()
    assert body["ok"] is True
    assert body["message"] is None

    return resp


async def leave_room(client: AsyncClient) -> Response:
    """
    테스트 상황을 만들기 위하여 leave_room을 호출한다.
    leave_room api 자체는 별도의 테스트로 검증되어야 한다.
    이 함수 내부에서는 최소한의 validation만 진행한다.
    """
    # ✅ TODO: 명세에 따라 body가 필요 없으면 json=None 제거
    resp = await client.post("/api/v1/rooms/current/leave")
    assert resp.status_code == status.HTTP_200_OK, resp.text

    body = resp.json()
    assert body["ok"] is True
    assert body["message"] is None

    return resp


@asynccontextmanager
async def skip_on_connect_snapshot(
    client: AsyncClient, room_id: RoomId
) -> AsyncIterator[SSEReader]:
    """ON CONNECT는 skip"""
    async with client.stream("GET", "/rt/v1/sse/rooms/current/state") as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")

        reader = SSEReader(r)

        first_body = await reader.read_one(timeout_s=2.0)
        assert first_body["event"] == SSEEventType.ON_CONNECT
        first_id = first_body.get("id")
        assert first_id
        first_data = first_body.get("data")
        assert first_data

        first_envelope = room_sse_validator.assert_envelope(first_data, ok=True)
        assert first_envelope.code == SSEEnvelopeCode.ROOM_STATE

        first_snapshot = first_envelope.data
        assert first_snapshot
        assert first_snapshot.room.id == room_id

        assert first_snapshot.last_event
        assert first_snapshot.last_event == RoomSnapshotType.ON_CONNECT

        # 최초 연결 snapshot이므로 logs는 비어 있어야 함
        assert first_snapshot.logs == []

        yield reader


def assert_room_snapshot_from_sse(payload: SSEPayload) -> RoomSnapshot:
    assert payload["event"] == SSEEventType.ROOM_EVENT
    sse_id = payload.get("id")
    assert sse_id
    sse_data = payload.get("data")
    assert sse_data

    envelope = room_sse_validator.assert_envelope(sse_data, ok=True)
    assert envelope.code == SSEEnvelopeCode.ROOM_STATE
    assert envelope.data
    return envelope.data
