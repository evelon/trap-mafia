from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.cases.phases.actions.common import (
    _ALREADY_DECIDED,
    _HAS_CURRENT_CASE,
    _IN_ROOM,
    _PHASE,
)
from app.schemas.case.action_responses.common_action import (
    ActionConflictCode,
    ActionForbiddenCode,
)
from app.schemas.case.action_responses.force_skip_discuss import (
    ForceSkipDiscussConflictResponse,
    ForceSkipDiscussForbiddenResponse,
    ForceSkipDiscussSuccessCode,
    ForceSkipDiscussSuccessResponse,
)
from app.schemas.case.actions.common import ActionReceipt

router = APIRouter()

_DISCUSS_PHASE = "DISCUSS"


@router.post(
    "/current/force-skip-discuss",
    summary="force_skip_discuss",
    response_model=ForceSkipDiscussSuccessResponse
    | ForceSkipDiscussConflictResponse
    | ForceSkipDiscussForbiddenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ForceSkipDiscussForbiddenResponse},
        status.HTTP_409_CONFLICT: {"model": ForceSkipDiscussConflictResponse},
    },
)
def force_skip_discuss():
    """
    POST /api/cases/current/force-skip-discuss

    의미:
    - DISCUSS phase를 강제 종료하고 NIGHT phase로 진행시키는 action을 접수한다.
    - MVP 단계에서는 권한(Host) 검증을 하지 않으며, 실제 phase 전환 및 SSE emit은 추후 구현한다.

    응답:
    - 200: action 접수 성공 (ActionReceipt)
    - 403: room/case 컨텍스트 없음
      - PERMISSION_DENIED_NOT_IN_ROOM
      - PERMISSION_DENIED_NOT_IN_CASE
    - 409: 동일 phase 컨텍스트에서 상태 충돌
      - PHASE_REJECTED_ALREADY_DECIDED
      - PHASE_REJECTED_CONFLICT_ACTION
    """
    # 403: no room / no current case context
    if not _IN_ROOM:
        return ForceSkipDiscussForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_ROOM,
            message="현재 참가 중인 방이 없습니다.",
            data=None,
            meta=None,
        )
    if not _HAS_CURRENT_CASE:
        return ForceSkipDiscussForbiddenResponse(
            ok=False,
            code=ActionForbiddenCode.PERMISSION_DENIED_NOT_IN_CASE,
            message="현재 진행 중인 케이스가 없습니다.",
            data=None,
            meta=None,
        )

    # 409: already decided in this phase
    if _ALREADY_DECIDED:
        return ForceSkipDiscussConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_ALREADY_DECIDED,
            message=None,
            data=None,
            meta=None,
        )

    # 409: action not allowed in current phase
    if _PHASE != _DISCUSS_PHASE:
        return ForceSkipDiscussConflictResponse(
            ok=False,
            code=ActionConflictCode.PHASE_REJECTED_CONFLICT_ACTION,
            message=None,
            data=None,
            meta=None,
        )

    return ForceSkipDiscussSuccessResponse(
        ok=True,
        code=ForceSkipDiscussSuccessCode.OK,
        message=None,
        data=ActionReceipt.mock(action_id=1, phase_id=UUID("00000000-0000-0000-0000-0000000000dd")),
        meta=None,
    )
