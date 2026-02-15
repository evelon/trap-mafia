from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.cases.phases.actions.common import (
    _ALREADY_DECIDED,
    _HAS_CURRENT_CASE,
    _IN_ROOM,
    _OCCUPIED_SEATS,
    _PHASE,
    _SELF_SEAT_NO,
)
from app.domain.constants import SEAT_NO_MAX_EXCLUSIVE, SEAT_NO_MIN
from app.schemas.case.action_responses.common_action import ActionConflictCode, ActionForbiddenCode
from app.schemas.case.action_responses.red_vote import (
    RedVoteBadRequestCode,
    RedVoteBadRequestResponse,
    RedVoteConflictCode,
    RedVoteConflictResponse,
    RedVoteForbiddenResponse,
    RedVoteNotFoundCode,
    RedVoteNotFoundResponse,
    RedVoteSuccessCode,
    RedVoteSuccessResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.case.actions.red_vote import RedVoteRequest
from app.schemas.common.validation import COMMON_422_RESPONSE

router = APIRouter()


@router.post(
    "/current/red-vote",
    summary="red_vote",
    response_model=RedVoteSuccessResponse
    | RedVoteBadRequestResponse
    | RedVoteNotFoundResponse
    | RedVoteForbiddenResponse
    | RedVoteConflictResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_422_RESPONSE,
        status.HTTP_400_BAD_REQUEST: {"model": RedVoteBadRequestResponse},
        status.HTTP_403_FORBIDDEN: {"model": RedVoteForbiddenResponse},
        status.HTTP_404_NOT_FOUND: {"model": RedVoteNotFoundResponse},
        status.HTTP_409_CONFLICT: {"model": RedVoteConflictResponse},
    },
)
def red_vote(body: RedVoteRequest):
    """
    POST /api/cases/current/red-vote

    의미:
    - NIGHT phase에서 red-vote 대상자를 지정하거나(skip 포함) action을 접수한다.
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
      - NIGHT_REJECTED_SELF_VOTE (스스로에게 투표 시도)
    """
    target = body.target_seat_no

    # 403: no room / no current case context
    if not _IN_ROOM:
        return RedVoteForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_ROOM,
            message="현재 참가 중인 방이 없습니다.",
            data=None,
            meta=None,
        )
    if not _HAS_CURRENT_CASE:
        return RedVoteForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_CASE,
            message="현재 진행 중인 케이스가 없습니다.",
            data=None,
            meta=None,
        )

    # 409: already decided in this phase
    if _ALREADY_DECIDED:
        return RedVoteConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_ALREADY_DECIDED,
            message=None,
            data=None,
            meta=None,
        )

    # 409: action not allowed in current phase
    if _PHASE != "NIGHT":
        return RedVoteConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_CONFLICT_ACTION,
            message=None,
            data=None,
            meta=None,
        )

    # 400: range validation (SeatNo)
    if target is not None and (target < SEAT_NO_MIN or target >= SEAT_NO_MAX_EXCLUSIVE):
        return RedVoteBadRequestResponse(
            ok=False,
            code=RedVoteBadRequestCode.INVALID_TARGET_SEAT_NO,
            message=None,
            data=None,
            meta=None,
        )

    # 200: skip
    if target is None:
        return RedVoteSuccessResponse(
            ok=True,
            code=RedVoteSuccessCode.OK,
            message=None,
            data=ActionReceipt.mock(action_id=1),
            meta=None,
        )

    # 409: self vote
    if target == _SELF_SEAT_NO:
        return RedVoteConflictResponse(
            ok=False,
            code=RedVoteConflictCode.NIGHT_REJECTED_SELF_VOTE,
            message=None,
            data=None,
            meta=None,
        )

    # 404: empty seat (mock occupied set)
    if target not in _OCCUPIED_SEATS:
        return RedVoteNotFoundResponse(
            ok=False,
            code=RedVoteNotFoundCode.TARGET_SEAT_EMPTY,
            message=None,
            data=None,
            meta=None,
        )

    # 200: accepted
    return RedVoteSuccessResponse(
        ok=True,
        code=RedVoteSuccessCode.OK,
        message=None,
        data=ActionReceipt.mock(action_id=1, phase_id=UUID("00000000-0000-0000-0000-0000000000aa")),
        meta=None,
    )
