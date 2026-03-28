from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.deps.require_in_case import CurrentCase
from app.core.error_codes import PermissionErrorCode
from app.core.exceptions import raise_forbidden
from app.core.security.auth import CurrentUser
from app.models.case import CasePlayer
from app.repositories.deps import CasePlayerRepoDep


async def get_current_case_player(
    user: CurrentUser,
    case: CurrentCase,
    case_player_repo: CasePlayerRepoDep,
) -> CasePlayer:
    """
    현재 인증된 유저가 현재 case에 속한 CasePlayer를 반환한다.

    Raises
    ------
    403 Forbidden
        유저가 해당 case의 player가 아닌 경우
    """
    case_player = await case_player_repo.get_by_case_id_and_user_id(
        case_id=case.id,
        user_id=user.id,
    )

    if case_player is None:
        raise_forbidden(
            code=PermissionErrorCode.PERMISSION_DENIED_NOT_IN_CASE,
            message="User is not a player in this case",
        )

    return case_player


CurrentCasePlayer = Annotated[CasePlayer, Depends(get_current_case_player)]
