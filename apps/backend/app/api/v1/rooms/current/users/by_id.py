from fastapi import APIRouter, status

from app.core.security.auth import CurrentUser
from app.schemas.common.ids import UserId
from app.schemas.room.response import (
    KickUserResponse,
)
from app.services.room import RoomServiceDep

router = APIRouter(prefix="/{user_id}")


@router.post(
    "/kick",
    summary="kick_user",
    response_model=KickUserResponse,
    status_code=status.HTTP_200_OK,
)
async def kick_user(
    user: CurrentUser,
    user_id: UserId,
    room_service: RoomServiceDep,
):
    """
    POST /api/v1/rooms/current/users/{user_id}/kick

    의미:
    - 특정 USER를 현재 ROOM에서 내보내기를 시도한다.
    - 성공 시 200 OK + KickUserMutation을 반환한다.
    - 대상이 해당 ROOM에 없더라도 200으로 응답하며, changed=False로 표현한다.

    주의:
    - 이 API는 대상 room에서의 멤버십 제거 여부만 보장한다.
    """
    mut = await room_service.kick_user(
        actor_user_id=user.id,
        target_user_id=user_id,
    )

    return KickUserResponse.success(data=mut)
