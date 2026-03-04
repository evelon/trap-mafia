from fastapi import APIRouter

from app.core.security.auth import CurrentUser
from app.mvp import MVP_ROOM_ID
from app.realtime.events.room_state_bus import RoomStateBusDep
from app.realtime.topics import RoomTopic
from app.schemas.room.sse_response import RoomStateCode, RoomStateResponse

router = APIRouter()


@router.post("/close")
async def close_room_state_stream(user: CurrentUser, room_state_bus: RoomStateBusDep):

    room_id = MVP_ROOM_ID

    # room:{room_id} 채널로 "닫아라" 이벤트 publish
    event = RoomStateResponse(
        ok=True,
        code=RoomStateCode.STREAM_CLOSE,
        message=None,
        data=None,  # 굳이 snapshot 필요 없음
    )
    room_topic = RoomTopic(room_id)
    await room_state_bus.publish(room_topic, event)
    return {"ok": True}
