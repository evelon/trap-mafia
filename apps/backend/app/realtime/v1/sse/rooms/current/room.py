from __future__ import annotations

from fastapi import APIRouter

from app.core.deps.require_in_room import CurrentRoomId
from app.core.security.auth import CurrentUser
from app.realtime_.sse.stream import sse_stream_response
from app.realtime_.streams.deps import RoomStateStreamDep

router = APIRouter()


@router.get("/state")
async def room_state_sse(
    user: CurrentUser, room_id: CurrentRoomId, room_state_stream: RoomStateStreamDep
):
    """GET /rt/v1/sse/rooms/current/state

    Notion: room_state
    - Auth: User
    - Permission: In Room

    Response (SSE)
    - event: ROOM_EVENT
    - id: 단조증가(연결 단위, MVP에서 1로 고정)
    - data: RoomStateResponse(JSON)

    Response (REST)
    - 403: PERMISSION_DENIED_NOT_IN_ROOM
    """
    stream = room_state_stream.stream(user.id, room_id)
    return sse_stream_response(stream)
