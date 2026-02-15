from uuid import UUID

from fastapi import APIRouter, status

from app.schemas.common.ids import RoomId
from app.schemas.common.validation import COMMON_422_RESPONSE
from app.schemas.room.action import CaseStartRequest
from app.schemas.room.response import (
    CaseStartConflictResponse,
    CaseStartForbiddenResponse,
    CaseStartMutation,
    CaseStartSuccessCode,
    CaseStartSuccessResponse,
    JoinRoomCode,
    JoinRoomMutation,
    JoinRoomReason,
    JoinRoomResponse,
    KickUserCode,
    KickUserMutation,
    KickUserReason,
    KickUserResponse,
    LeaveRoomCode,
    LeaveRoomMutation,
    LeaveRoomReason,
    LeaveRoomResponse,
)

router = APIRouter()


@router.post(
    "/{room_id}/join",
    summary="join_room",
    response_model=JoinRoomResponse,
    status_code=status.HTTP_200_OK,
)
def join_room(room_id: RoomId):
    """
    POST /api/rooms/{room_id}/join

    의미:
    - 현재 사용자가 특정 ROOM에 참가를 시도한다.
    - 성공 시 200 OK + JoinRoomMutation을 반환한다.
    - 이미 참가 중인 경우에도 200으로 응답하며, changed=False로 표현한다.

    비고:
    - 실제 ROOM_FULL, membership 검증 로직은 추후 구현 예정이다.
    """
    # MVP NOTE:
    # - Spec currently treats only one room_id as valid.
    # - Real membership change detection and ROOM_FULL handling will be implemented later.
    #
    # For now, return a deterministic "joined" response.
    data = JoinRoomMutation(
        changed=True,
        reason=JoinRoomReason.JOINED,
    )
    return JoinRoomResponse(
        ok=True,
        code=JoinRoomCode.OK,
        message=None,
        data=data,
        meta=None,
    )


@router.post(
    "/current/leave",
    summary="leave_room",
    response_model=LeaveRoomResponse,
    status_code=status.HTTP_200_OK,
)
def leave_room():
    """
    POST /api/rooms/current/leave

    의미:
    - 현재 사용자가 자신이 속한 ROOM에서 나가기를 시도한다.
    - 성공 시 200 OK + LeaveRoomMutation을 반환한다.
    - 이미 방에 속해 있지 않은 경우에도 200으로 응답하며, changed=False로 표현한다.
    """
    data = LeaveRoomMutation(changed=True, reason=LeaveRoomReason.LEFT)
    return LeaveRoomResponse(ok=True, code=LeaveRoomCode.OK, data=data, meta=None)


@router.post(
    "/current/users/{user_id}/kick",
    summary="kick_user",
    response_model=KickUserResponse,
    status_code=status.HTTP_200_OK,
)
def kick_user(user_id: UUID):
    """
    POST /api/rooms/current/users/{user_id}/kick

    의미:
    - 특정 USER를 현재 ROOM에서 내보내기를 시도한다.
    - 성공 시 200 OK + KickUserMutation을 반환한다.
    - 대상이 해당 ROOM에 없더라도 200으로 응답하며, changed=False로 표현한다.

    주의:
    - 이 API는 대상 room에서의 멤버십 제거 여부만 보장한다.
    """
    data = KickUserMutation(
        subject_id=user_id,
        changed=False,
        reason=KickUserReason.NOT_IN_ROOM,
    )
    return KickUserResponse(ok=True, code=KickUserCode.OK, data=data, meta=None)


@router.post(
    "/current/case-start",
    summary="case_start",
    response_model=CaseStartSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_422_RESPONSE,
        status.HTTP_403_FORBIDDEN: {"model": CaseStartForbiddenResponse},
        status.HTTP_409_CONFLICT: {"model": CaseStartConflictResponse},
    },
)
def case_start(body: CaseStartRequest):
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
    data = CaseStartMutation()
    return CaseStartSuccessResponse(ok=True, code=CaseStartSuccessCode.OK, data=data, meta=None)


# POST /current/force-skip
