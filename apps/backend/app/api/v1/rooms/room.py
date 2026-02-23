from uuid import UUID

from fastapi import APIRouter, Request, status

from app.core.auth import ACCESS_TOKEN, JwtHandlerDep
from app.core.exceptions import EnvelopeException
from app.schemas.common.error import AuthTokenErrorCode
from app.schemas.common.ids import RoomId
from app.schemas.common.response import COMMON_422_VALIDATION_RESPONSE
from app.schemas.room.action import CaseStartRequest
from app.schemas.room.mutation import (
    CaseStartMutation,
    KickUserMutation,
    KickUserReason,
    LeaveRoomCode,
)
from app.schemas.room.response import (
    CaseStartConflictResponse,
    CaseStartForbiddenResponse,
    CaseStartSuccessCode,
    CaseStartSuccessResponse,
    JoinRoomCode,
    JoinRoomResponse,
    KickUserCode,
    KickUserResponse,
    LeaveRoomResponse,
)
from app.services.room import RoomServiceDep

router = APIRouter()


@router.post(
    "/{room_id}/join",
    summary="join_room",
    response_model=JoinRoomResponse,
    status_code=status.HTTP_200_OK,
)
async def join_room(
    room_id: RoomId,
    request: Request,
    room_service: RoomServiceDep,
    jwt_handler: JwtHandlerDep,
) -> JoinRoomResponse:
    """
    POST /api/v1/rooms/{room_id}/join
    - access_token 쿠키에서 user_id를 추출
    - RoomService.join_room 호출
    - JoinRoomResponse(Envelope)로 반환
    """
    access_token = request.cookies.get(ACCESS_TOKEN)
    if not access_token:
        raise EnvelopeException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            response_code=AuthTokenErrorCode.AUTH_TOKEN_NOT_INCLUDED,
        )

    user_id_str = jwt_handler.extract_user_id_from_token(access_token, ACCESS_TOKEN)
    user_id = UUID(user_id_str)

    mut = await room_service.join_room(user_id=user_id, room_id=room_id)

    return JoinRoomResponse(
        ok=True,
        code=JoinRoomCode.OK,
        message=None,
        data=mut,
        meta=None,
    )


@router.post(
    "/current/leave",
    summary="leave_room",
    response_model=LeaveRoomResponse,
    status_code=status.HTTP_200_OK,
)
async def leave_room(
    request: Request,
    room_service: RoomServiceDep,
    jwt_handler: JwtHandlerDep,
) -> LeaveRoomResponse:
    """
    POST /api/v1/rooms/current/leave
    - access_token 쿠키에서 user_id를 추출
    - RoomService.leave_current_room 호출
    - LeaveRoomResponse(Envelope)로 반환
    """
    access_token = request.cookies.get(ACCESS_TOKEN)
    if not access_token:
        raise EnvelopeException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            response_code=AuthTokenErrorCode.AUTH_TOKEN_NOT_INCLUDED,
        )

    user_id_str = jwt_handler.extract_user_id_from_token(access_token, ACCESS_TOKEN)
    user_id = UUID(user_id_str)

    mut = await room_service.leave_current_room(user_id=user_id)

    return LeaveRoomResponse(
        ok=True,
        code=LeaveRoomCode.OK,
        message=None,
        data=mut,
        meta=None,
    )


@router.post(
    "/current/users/{user_id}/kick",
    summary="kick_user",
    response_model=KickUserResponse,
    status_code=status.HTTP_200_OK,
)
async def kick_user(user_id: UUID):
    """
    POST /api/rooms/current/users/{user_id}/kick

    의미:
    - 특정 USER를 현재 ROOM에서 내보내기를 시도한다.
    - 성공 시 200 OK + KickUserMutation을 반환한다.
    - 대상이 해당 ROOM에 없더라도 200으로 응답하며, changed=False로 표현한다.

    주의:
    - 이 API는 대상 room에서의 멤버십 제거 여부만 보장한다.
    """
    mut = KickUserMutation(
        subject_id=user_id,
        changed=False,
        reason=KickUserReason.NOT_IN_ROOM,
    )
    return KickUserResponse(ok=True, code=KickUserCode.OK, data=mut, meta=None)


@router.post(
    "/current/case-start",
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
    return CaseStartSuccessResponse(ok=True, code=CaseStartSuccessCode.OK, data=mut, meta=None)


# POST /current/force-skip
