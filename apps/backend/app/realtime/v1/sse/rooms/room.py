from __future__ import annotations

import json
from typing import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse, StreamingResponse

from app.schemas.room.sse_response import RoomStateCode, RoomStateResponse
from app.schemas.room.state import RoomInfo, RoomSnapshot

router = APIRouter()


# NOTE: MVP mock 구현
# - 실제 구현에서는 "현재 유저가 속한 room_id"를 DB/Redis에서 조회합니다.
# - JWT 도입 전까지는 FE 연동을 위해 헤더로 room_id를 흉내냅니다.
#   - X-Room-Id: string (방에 속하지 않은 경우 미전달)
#   - X-User-Id: string (Auth mock; 향후 JWT로 대체)


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


async def _forbidden_not_in_room() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "ok": False,
            "code": "PERMISSION_DENIED_NOT_IN_ROOM",
            "message": "The user is not in a room.",
            "data": None,
        },
    )


async def _mvp_snapshot(room_id: UUID) -> RoomSnapshot:
    # MVP: RoomInfo/RoomSnapshot 기본값으로 충분
    # host_user_id 등은 실제 구현 시 DB에서 채워 넣으면 됩니다.
    return RoomSnapshot(room=RoomInfo(id=room_id))


@router.get("/current")
async def room_state_sse(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_room_id: str | None = Header(default=None, alias="X-Room-Id"),
):
    """GET /rt/v1/sse/rooms/current

    Notion: room_state
    - Auth: User (MVP: X-User-Id 헤더, 추후 JWT로 대체)
    - Permission: In Room (MVP: X-Room-Id 헤더로 대체)

    Response (SSE)
    - event: room_state
    - id: 단조증가(연결 단위, MVP)
    - data: RoomStateResponse(JSON)

    Response (REST)
    - 403: PERMISSION_DENIED_NOT_IN_ROOM
    """

    # MVP: "In Room"만 목업한다.
    if x_room_id is None:
        return _forbidden_not_in_room()

    snapshot = await _mvp_snapshot(UUID(x_room_id))

    payload = RoomStateResponse(
        ok=True,
        code=RoomStateCode.SNAPSHOT_ON_CONNECT,
        message=None,
        data=snapshot,
    )

    async def gen() -> AsyncIterator[str]:
        # MVP: 연결 직후 스냅샷 1회만 보내고 종료
        yield await _sse_frame(event="room_state", id_=1, data=payload.model_dump())

    return StreamingResponse(gen(), media_type="text/event-stream")
