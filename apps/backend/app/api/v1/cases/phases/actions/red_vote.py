from typing import Never
from uuid import UUID

from fastapi import APIRouter, status

from app.core.deps.current_case_player import CurrentCasePlayer
from app.core.deps.require_in_case import CurrentCase
from app.core.error_codes import BadRequestErrorCode, ConflictErrorCode
from app.core.exceptions import raise_bad_request, raise_conflict
from app.domain.case_logic.night import NightRuleViolationError, NightRuleViolationReason
from app.domain.exceptions.common import EntityNotFoundError
from app.schemas.case.action_responses.red_vote import (
    RedVoteBadRequestResponse,
    RedVoteConflictResponse,
    RedVoteForbiddenResponse,
    RedVoteNotFoundResponse,
    RedVoteSuccessCode,
    RedVoteSuccessResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.case.actions.red_vote import RedVoteRequest
from app.schemas.common.response import COMMON_422_VALIDATION_RESPONSE
from app.services.deps import CaseServiceDep

router = APIRouter()


def _raise_red_vote_api_error(e: Exception) -> Never:
    if isinstance(e, NightRuleViolationError):
        if e.reason == NightRuleViolationReason.INVALID_TARGET_SEAT:
            raise_bad_request(
                code=BadRequestErrorCode.BAD_REQUEST_INVALID_TARGET_SEAT,
                message=str(e),
            )
        if e.reason == NightRuleViolationReason.SELF_VOTE:
            raise_conflict(
                code=ConflictErrorCode.CONFLICT_NIGHT_REJECTED_SELF_VOTE,
                message=str(e),
            )
        if e.reason == NightRuleViolationReason.ALREADY_ACTED:
            raise_conflict(
                code=ConflictErrorCode.CONFLICT_PHASE_REJECTED_ALREADY_DECIDED,
                message=str(e),
            )
        if e.reason in (
            NightRuleViolationReason.NOT_NIGHT_PHASE,
            NightRuleViolationReason.NOT_ALIVE,
        ):
            raise_conflict(
                code=ConflictErrorCode.CONFLICT_PHASE_REJECTED_CONFLICT_ACTION,
                message=str(e),
            )

    if isinstance(e, EntityNotFoundError):
        if e.ref.entity == "CurrentPhase":
            raise_conflict(
                code=ConflictErrorCode.CONFLICT_PHASE_NOT_FOUND,
                message=str(e),
            )
        if e.ref.entity == "Case":
            raise_conflict(
                code=ConflictErrorCode.CONFLICT_CASE_NOT_FOUND,
                message=str(e),
            )
        if e.ref.entity == "Actor":
            raise_conflict(
                code=ConflictErrorCode.CONFLICT_ACTOR_NOT_FOUND,
                message=str(e),
            )

    raise e


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
        **COMMON_422_VALIDATION_RESPONSE,
        status.HTTP_400_BAD_REQUEST: {"model": RedVoteBadRequestResponse},
        status.HTTP_403_FORBIDDEN: {"model": RedVoteForbiddenResponse},
        status.HTTP_404_NOT_FOUND: {"model": RedVoteNotFoundResponse},
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
    try:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=case_player.id,
            target_seat_no=body.target_seat_no,
        )
    except Exception as e:
        _raise_red_vote_api_error(e)

    # 200: accepted
    return RedVoteSuccessResponse(
        ok=True,
        code=RedVoteSuccessCode.OK,
        message=None,
        data=ActionReceipt.mock(action_id=1, phase_id=UUID("00000000-0000-0000-0000-0000000000aa")),
        meta=None,
    )
