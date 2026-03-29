from uuid import UUID

from fastapi import APIRouter, status

from app.core.deps.current_case_player import CurrentCasePlayer
from app.core.deps.require_in_case import CurrentCase
from app.schemas.case.action_responses.red_vote import (
    RedVoteBadRequestResponse,
    RedVoteConflictResponse,
    RedVoteForbiddenResponse,
    RedVoteSuccessCode,
    RedVoteSuccessResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.case.actions.red_vote import RedVoteRequest
from app.schemas.common.response import COMMON_422_VALIDATION_RESPONSE
from app.services.deps import CaseServiceDep

router = APIRouter()


@router.post(
    "/current/red-vote",
    summary="red_vote",
    response_model=RedVoteSuccessResponse
    | RedVoteBadRequestResponse
    | RedVoteForbiddenResponse
    | RedVoteConflictResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_422_VALIDATION_RESPONSE,
        status.HTTP_400_BAD_REQUEST: {"model": RedVoteBadRequestResponse},
        status.HTTP_403_FORBIDDEN: {"model": RedVoteForbiddenResponse},
        status.HTTP_409_CONFLICT: {"model": RedVoteConflictResponse},
    },
)
async def red_vote(
    body: RedVoteRequest,
    case_player: CurrentCasePlayer,
    case: CurrentCase,
    case_service: CaseServiceDep,
):
    """
    POST /api/cases/current/red-vote

    의미:
    - 현재 case/phase/player 컨텍스트를 검증한 뒤 red-vote 또는 skip action을 접수한다.

    응답:
    - 200: action 접수 성공 (ActionReceipt)
    - 400: seat_no 범위 오류
    - 403: room/case/player 컨텍스트 없음
      - PERMISSION_DENIED_NOT_IN_ROOM
      - PERMISSION_DENIED_NOT_IN_CASE
      - 유저가 현재 case의 player가 아님
    - 409: 동일 phase 컨텍스트에서 상태 충돌
      - PHASE_REJECTED_ALREADY_DECIDED
      - PHASE_REJECTED_CONFLICT_ACTION
      - NIGHT_REJECTED_SELF_VOTE
      - CONFLICT_CASE_NOT_FOUND
      - CONFLICT_PHASE_NOT_FOUND
      - CONFLICT_ACTOR_NOT_FOUND
    """
    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=case_player.id,
        target_seat_no=body.target_seat_no,
    )

    # 200: accepted
    return RedVoteSuccessResponse(
        ok=True,
        code=RedVoteSuccessCode.OK,
        message=None,
        data=ActionReceipt.mock(action_id=1, phase_id=UUID("00000000-0000-0000-0000-0000000000aa")),
        meta=None,
    )
