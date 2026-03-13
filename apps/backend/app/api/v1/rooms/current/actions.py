from fastapi import APIRouter, status

from app.core.security.auth import CurrentUser
from app.schemas.common.response import COMMON_422_VALIDATION_RESPONSE
from app.schemas.room.action import CaseStartRequest
from app.schemas.room.mutation import (
    CaseStartMutation,
)
from app.schemas.room.response import (
    CaseStartConflictResponse,
    CaseStartForbiddenResponse,
    CaseStartSuccessResponse,
    LeaveRoomResponse,
)
from app.services.deps import RoomServiceDep

router = APIRouter()


@router.post(
    "/leave",
    summary="leave_room",
    response_model=LeaveRoomResponse,
    status_code=status.HTTP_200_OK,
)
async def leave_room(
    user: CurrentUser,
    room_service: RoomServiceDep,
) -> LeaveRoomResponse:
    """
    POST /api/v1/rooms/current/leave
    - access_token 쿠키에서 user_id를 추출
    - RoomService.leave_current_room 호출
    - LeaveRoomResponse(Envelope)로 반환
    """
    mut = await room_service.leave_current_room(user_id=user.id)

    return LeaveRoomResponse.success(data=mut)


@router.post(
    "/case-start",
    summary="case_start",
    response_model=CaseStartSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_422_VALIDATION_RESPONSE,
        status.HTTP_403_FORBIDDEN: {"model": CaseStartForbiddenResponse},
        status.HTTP_409_CONFLICT: {"model": CaseStartConflictResponse},
    },
)
async def case_start(body: CaseStartRequest):
    """
    POST /api/rooms/current/case-start

    의미:
    - 현재 ROOM에서 case 시작을 시도한다.
    - 성공 시 200 OK + CaseStartMutation을 반환한다.
    - 권한/조건 불충족 시 403 또는 409로 분리 응답한다.

    상태 코드 기준:
    - 403: room에 속해 있지 않거나 시작 권한이 없는 경우
    - 409: room 상태가 case 시작 조건을 만족하지 않는 경우
    """
    mut = CaseStartMutation()
    return CaseStartSuccessResponse.success(data=mut)


# POST /current/force-skip
