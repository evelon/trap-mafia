from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.cases.phases.actions.common import (
    _ALREADY_DECIDED,
    _DISCUSS_HAS_TOKEN_FOR_INIT,
    _DISCUSS_PHASE,
    _HAS_CURRENT_CASE,
    _IN_ROOM,
    _OCCUPIED_SEATS,
    _PHASE,
    _SELF_SEAT_NO,
)
from app.domain.constants import SEAT_NO_MAX_EXCLUSIVE, SEAT_NO_MIN
from app.schemas.case.action_responses.common_action import ActionConflictCode, ActionForbiddenCode
from app.schemas.case.action_responses.init_blue_vote import (
    InitBlueVoteBadRequestCode,
    InitBlueVoteBadRequestResponse,
    InitBlueVoteConflictCode,
    InitBlueVoteConflictResponse,
    InitBlueVoteForbiddenResponse,
    InitBlueVoteNotFoundCode,
    InitBlueVoteNotFoundResponse,
    InitBlueVoteSuccessCode,
    InitBlueVoteSuccessResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.case.actions.init_blue_vote import InitBlueVoteRequest

router = APIRouter()


@router.post(
    "/current/init-blue-vote",
    summary="init_blue_vote",
    response_model=InitBlueVoteSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": InitBlueVoteBadRequestResponse},
        status.HTTP_403_FORBIDDEN: {"model": InitBlueVoteForbiddenResponse},
        status.HTTP_404_NOT_FOUND: {"model": InitBlueVoteNotFoundResponse},
        status.HTTP_409_CONFLICT: {"model": InitBlueVoteConflictResponse},
    },
)
def init_blue_vote(body: InitBlueVoteRequest):
    """
    POST /api/cases/current/init-blue-vote

    의미:
    - DISCUSS phase에서 플레이어가 blue-vote의 대상자를 지정하여 VOTE phase 시작을 요청한다.
    - MVP 목업 구현이며, 실제 phase 검증 및 SSE emit은 추후 구현한다.

    응답:
    - 200: action 접수 성공 (ActionReceipt)
    - 400: seat_no 범위 오류 (SeatNo)
    - 403: room/case 컨텍스트 없음
      - PERMISSION_DENIED_NOT_IN_ROOM
      - PERMISSION_DENIED_NOT_IN_CASE
    - 404: TARGET_SEAT_EMPTY (대상 seat에 user 없음)
    - 409: 동일 phase 컨텍스트에서 상태 충돌
      - PHASE_REJECTED_ALREADY_DECIDED
      - PHASE_REJECTED_CONFLICT_ACTION
      - DISCUSS_REJECTED_NO_TOKEN_INIT
      - DISCUSS_REJECTED_SELF_VOTE_INIT
    """
    target = body.target_seat_no

    # 403: no room / no current case context
    if not _IN_ROOM:
        return InitBlueVoteForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_ROOM,
            message="현재 참가 중인 방이 없습니다.",
            data=None,
            meta=None,
        )
    if not _HAS_CURRENT_CASE:
        return InitBlueVoteForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_CASE,
            message="현재 진행 중인 케이스가 없습니다.",
            data=None,
            meta=None,
        )

    # 409: already decided in this phase
    if _ALREADY_DECIDED:
        return InitBlueVoteConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_ALREADY_DECIDED,
            message=None,
            data=None,
            meta=None,
        )

    # 409: action not allowed in current phase
    if _PHASE != _DISCUSS_PHASE:
        return InitBlueVoteConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_CONFLICT_ACTION,
            message=None,
            data=None,
            meta=None,
        )

    # 400: range validation (SeatNo)
    if target < SEAT_NO_MIN or target >= SEAT_NO_MAX_EXCLUSIVE:
        return InitBlueVoteBadRequestResponse(
            ok=False,
            code=InitBlueVoteBadRequestCode.INVALID_TARGET_SEAT_NO,
            message=None,
            data=None,
            meta=None,
        )

    # 409: no token for init
    if not _DISCUSS_HAS_TOKEN_FOR_INIT:
        return InitBlueVoteConflictResponse(
            ok=False,
            code=InitBlueVoteConflictCode.DISCUSS_REJECTED_NO_TOKEN_INIT,
            message=None,
            data=None,
            meta=None,
        )

    # 409: self vote init
    if target == _SELF_SEAT_NO:
        return InitBlueVoteConflictResponse(
            ok=False,
            code=InitBlueVoteConflictCode.DISCUSS_REJECTED_SELF_VOTE_INIT,
            message=None,
            data=None,
            meta=None,
        )

    # 404: empty seat (mock occupied set)
    if target not in _OCCUPIED_SEATS:
        return InitBlueVoteNotFoundResponse(
            ok=False,
            code=InitBlueVoteNotFoundCode.TARGET_SEAT_EMPTY,
            message=None,
            data=None,
            meta=None,
        )

    # 200: accepted
    return InitBlueVoteSuccessResponse(
        ok=True,
        code=InitBlueVoteSuccessCode.OK,
        message=None,
        data=ActionReceipt.mock(action_id=1, phase_id=UUID("00000000-0000-0000-0000-0000000000bb")),
        meta=None,
    )
