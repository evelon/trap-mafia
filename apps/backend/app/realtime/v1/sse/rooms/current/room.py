from __future__ import annotations

import json
from typing import AsyncIterator
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.deps.require_in_room import CurrentRoomId
from app.realtime.events.room_state_bus import RoomStateBusDep
from app.realtime.topics import RoomTopic
from app.schemas.room.sse_response import RoomStateCode, RoomStateResponse
from app.schemas.room.state import RoomInfo, RoomSnapshot

router = APIRouter()


# NOTE: MVP mock 구현
# - 실제 구현에서는 "현재 유저가 속한 room_id"를 DB/Redis에서 조회합니다.


async def _sse_frame(*, event: str, data: dict, id_: int | None = None) -> str:
    """SSE 프레임을 생성합니다.

    - data는 한 줄 JSON으로 넣습니다(줄바꿈이 있으면 data:가 여러 줄로 쪼개져야 함).
    """

    lines: list[str] = [f"event: {event}"]
    if id_ is not None:
        lines.append(f"id: {id_}")

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    lines.append(f"data: {payload}")
    return "\n".join(lines) + "\n\n"


async def _mvp_snapshot(room_id: UUID) -> RoomSnapshot:
    # MVP: RoomInfo/RoomSnapshot 기본값으로 충분
    # host_user_id 등은 실제 구현 시 DB에서 채워 넣으면 됩니다.
    return RoomSnapshot(
        room=RoomInfo(id=room_id, room_name="test_name", host_user_id=None, created_at="")
    )


@router.get("/state")
async def room_state_sse(
    room_id: CurrentRoomId,
    room_state_bus: RoomStateBusDep,
):
    """GET /rt/v1/sse/rooms/current

    Notion: room_state
    - Auth: User
    - Permission: In Room

    Response (SSE)
    - event: room_state
    - id: 단조증가(연결 단위, MVP)
    - data: RoomStateResponse(JSON)

    Response (REST)
    - 403: PERMISSION_DENIED_NOT_IN_ROOM
    """

    snapshot = await _mvp_snapshot(room_id)

    payload = RoomStateResponse(
        ok=True,
        code=RoomStateCode.SNAPSHOT_ON_CONNECT,
        message=None,
        data=snapshot,
    )

    async def gen() -> AsyncIterator[str]:
        yield await _sse_frame(event="room_state", id_=1, data=payload.model_dump(mode="json"))

        room_state_iter = room_state_bus.subscribe(RoomTopic(room_id))
        async for room_state in room_state_iter:
            yield await _sse_frame(event="room_state", data=room_state.model_dump(mode="json"))

            if room_state.code == RoomStateCode.STREAM_CLOSE:
                break

    return StreamingResponse(gen(), media_type="text/event-stream")
