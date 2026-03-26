from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.deps.require_in_room import CurrentRoomId
from app.core.error_codes import ConflictErrorCode
from app.core.exceptions import raise_conflict
from app.core.security.auth import CurrentUser
from app.models.case import Case
from app.repositories.deps import CaseRepoDep


async def get_current_case(
    user: CurrentUser, room_id: CurrentRoomId, case_repo: CaseRepoDep
) -> Case:
    case_ = await case_repo.get_running_by_room_id(room_id=room_id)
    if case_ is None:
        raise_conflict(code=ConflictErrorCode.CONFLICT_NOT_ON_CASE)
    return case_


RequireInCase = Depends(get_current_case)
CurrentCase = Annotated[Case, Depends(get_current_case)]
