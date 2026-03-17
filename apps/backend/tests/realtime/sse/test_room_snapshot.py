import json
from uuid import UUID

from fastapi import status
from httpx import AsyncClient

from app.mvp import MVP_ROOM_ID
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType
from tests._helpers.auth import UserAuth
from tests._helpers.room_actions import join_room
from tests._helpers.sse import SSEReader


async def test_room_state_sse_requires_membership_403(
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
):
    # join_room을 하지 않았으므로 403이 떠야 함
    async with sse_client.stream("GET", "/rt/v1/sse/rooms/current/state") as r:
        assert r.status_code == status.HTTP_403_FORBIDDEN

        content_type = r.headers.get("content-type", "")
        assert content_type.startswith("application/json")

        body = (await r.aread()).decode("utf-8")
        # json parse는 프로젝트 helper가 있으면 그걸 쓰는 게 좋음

        env = json.loads(body)
        assert env["ok"] is False
        assert env["code"] == "PERMISSION_DENIED_NOT_IN_ROOM"
        # message는 명세에 맞게 (None일 수도, 문자열일 수도)
        # assert env["message"] == "..."


async def test_room_state_sse_snapshot_after_join_room(
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
):
    room_id = MVP_ROOM_ID
    # 먼저 join_room 수행
    await join_room(sse_client, room_id)

    # 그 다음 SSE 구독하면 snapshot 이벤트가 와야 함
    async with sse_client.stream("GET", "/rt/v1/sse/rooms/current/state") as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")

        reader = SSEReader(r)
        msg = await reader.read_one(timeout_s=2.0)
        assert msg["event"] == SSEEventType.ON_CONNECT
        assert msg.get("id") is not None

        body = msg["data"]
        assert body["ok"] is True
        assert body["code"] == SSEEnvelopeCode.ROOM_STATE
        assert body["message"] is None

        room_id = body["data"]["room"]["id"]
        assert room_id == str(MVP_ROOM_ID)
        UUID(room_id)  # 형식 깨짐 방지
