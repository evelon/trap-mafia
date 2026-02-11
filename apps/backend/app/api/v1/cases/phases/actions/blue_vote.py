from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.cases.phases.actions.common import (
    _ALREADY_DECIDED,
    _HAS_CURRENT_CASE,
    _IN_ROOM,
    _PHASE,
)
from app.schemas.case.action_responses.blue_vote import (
    BlueVoteConflictCode,
    BlueVoteConflictResponse,
    BlueVoteForbiddenResponse,
    BlueVoteSuccessCode,
    BlueVoteSuccessResponse,
)
from app.schemas.case.action_responses.common_action import (
    ActionConflictCode,
    ActionForbiddenCode,
)
from app.schemas.case.actions.blue_vote import BlueVoteRequest
from app.schemas.case.actions.common import ActionReceipt

router = APIRouter()


# NOTE: MVP mock flag for vote token
_VOTE_HAS_TOKEN = True
_VOTE_PHASE = "VOTE"


@router.post(
    "/current/blue-vote",
    summary="blue_vote",
    response_model=BlueVoteSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": BlueVoteForbiddenResponse},
        status.HTTP_409_CONFLICT: {"model": BlueVoteConflictResponse},
    },
)
def blue_vote(body: BlueVoteRequest):
    """
    POST /api/cases/current/blue-vote

    의미:
    - VOTE phase에서 플레이어가 YES / NO / SKIP 중 하나를 선택한다.
    - MVP 목업 구현이며, 실제 phase 전환 및 SSE emit은 추후 구현한다.

    응답:
    - 200: action 접수 성공 (ActionReceipt)
    - 403: room/case 컨텍스트 없음
      - PERMISSION_DENIED_NOT_IN_ROOM
      - PERMISSION_DENIED_NOT_IN_CASE
    - 409: 동일 phase 컨텍스트에서 상태 충돌
      - PHASE_REJECTED_ALREADY_DECIDED
      - PHASE_REJECTED_CONFLICT_ACTION
      - VOTE_REJECTED_NO_TOKEN
    """

    # 403: no room / no current case context
    if not _IN_ROOM:
        return BlueVoteForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_ROOM,
            message="현재 참가 중인 방이 없습니다.",
            data=None,
            meta=None,
        )
    if not _HAS_CURRENT_CASE:
        return BlueVoteForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_CASE,
            message="현재 진행 중인 케이스가 없습니다.",
            data=None,
            meta=None,
        )

    # 409: already decided in this phase
    if _ALREADY_DECIDED:
        return BlueVoteConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_ALREADY_DECIDED,
            message=None,
            data=None,
            meta=None,
        )

    # 409: action not allowed in current phase
    if _PHASE != _VOTE_PHASE:
        return BlueVoteConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_CONFLICT_ACTION,
            message=None,
            data=None,
            meta=None,
        )

    # 409: no token for vote
    if not _VOTE_HAS_TOKEN:
        return BlueVoteConflictResponse(
            ok=False,
            code=BlueVoteConflictCode.VOTE_REJECTED_NO_TOKEN,
            message=None,
            data=None,
            meta=None,
        )

    # 200: accepted
    return BlueVoteSuccessResponse(
        ok=True,
        code=BlueVoteSuccessCode.OK,
        message=None,
        data=ActionReceipt.mock(
            action_id=1,
            phase_id=UUID("00000000-0000-0000-0000-0000000000cc"),
        ),
        meta=None,
    )
