import json
from uuid import UUID

from httpx import AsyncClient

from app.mvp import MVP_ROOM_ID
from tests._helpers.auth import UserAuth
from tests._helpers.sse import SSEReader


async def _join_room(client: AsyncClient) -> None:
    """
    room SSE 구독 전제 조건을 만족시키기 위해 join_room을 호출한다.

    NOTE: 실제 명세에 맞게 payload/headers 등을 조정해야 함.
    """
    # ✅ TODO: 명세에 따라 body가 필요 없으면 json=None 제거
    resp = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    # envelope 형태를 쓰는 프로젝트라면 아래처럼 최소한의 계약만 고정
    assert body["ok"] is True
    assert body["message"] is None


async def test_room_state_sse_requires_membership_403(
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
):
    # join_room을 하지 않았으므로 403이 떠야 함
    async with sse_client.stream("GET", "/rt/v1/sse/rooms/current/state") as r:
        assert r.status_code == 403

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
    # 먼저 join_room 수행
    await _join_room(sse_client)

    # 그 다음 SSE 구독하면 snapshot 이벤트가 와야 함
    async with sse_client.stream("GET", "/rt/v1/sse/rooms/current/state") as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")

        reader = SSEReader(r)
        msg = await reader.read_one(timeout_s=2.0)
        assert msg["event"] == "room_state"
        assert msg.get("id") is not None

        body = msg["data"]
        assert body["ok"] is True
        assert body["code"] == "SNAPSHOT_ON_CONNECT"
        assert body["message"] is None

        room_id = body["data"]["room"]["id"]
        assert room_id == str(MVP_ROOM_ID)
        UUID(room_id)  # 형식 깨짐 방지
