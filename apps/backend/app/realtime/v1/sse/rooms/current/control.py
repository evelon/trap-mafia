from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.security.auth import CurrentUser
from app.domain.events import RoomEventDelta, RoomEventType
from app.infra.pubsub.bus.deps import RoomEventBusDep
from app.infra.pubsub.topics import RoomTopic
from app.mvp import MVP_ROOM_ID
from app.schemas.room.sse_response import RoomStateEnvelope
from app.schemas.sse.response import SSEEnvelopeCode

router = APIRouter()


@router.post("/close")
async def close_room_state_stream(
    user: CurrentUser, room_state_bus: RoomEventBusDep
) -> RoomStateEnvelope:

    room_id = MVP_ROOM_ID

    # room:{room_id} 채널로 "닫아라" 이벤트 publish
    event_resp = RoomStateEnvelope(
        ok=True,
        code=SSEEnvelopeCode.ROOM_STATE,
        message=None,
        data=None,  # 굳이 snapshot 필요 없음
    )

    event_msg = RoomEventDelta(
        type=RoomEventType.STREAM_CLOSE, user_id=user.id, ts=datetime.now(timezone.utc)
    )
    room_topic = RoomTopic(room_id)
    await room_state_bus.publish(room_topic, event_msg)
    return event_resp
