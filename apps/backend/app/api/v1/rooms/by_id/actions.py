from fastapi import APIRouter, status

from app.core.security.auth import CurrentUser
from app.infra.pubsub.bus.deps import RoomEventBusDep
from app.schemas.common.ids import RoomId
from app.schemas.room.response import JoinRoomResponse
from app.services.deps import RoomServiceDep

router = APIRouter()


@router.post(
    "/join",
    summary="join_room",
    response_model=JoinRoomResponse,
    status_code=status.HTTP_200_OK,
)
async def join_room(
    room_id: RoomId,
    user: CurrentUser,
    room_service: RoomServiceDep,
    room_event_bus: RoomEventBusDep,
) -> JoinRoomResponse:
    """
    POST /api/v1/rooms/{room_id}/join
    - access_token 쿠키에서 user_id를 추출
    - RoomService.join_room 호출
    - JoinRoomResponse(Envelope)로 반환
    """
    mut = await room_service.join_room(user_id=user.id, room_id=room_id)

    return JoinRoomResponse.success(data=mut)
