from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.exceptions import raise_forbidden
from app.core.security.auth import CurrentUser
from app.mvp import MVP_ROOM_ID
from app.repositories.deps import RoomMemberRepoDep
from app.schemas.common.error import PermissionErrorCode
from app.schemas.common.ids import RoomId


async def get_current_room_id(user: CurrentUser, room_member_repo: RoomMemberRepoDep) -> RoomId:
    room_member = await room_member_repo.get_active_by_user_id(user_id=user.id)
    if room_member is None:
        raise_forbidden(code=PermissionErrorCode.PERMISSION_DENIED_NOT_IN_ROOM)
    # room_id = room_member.room_id
    # MVP
    room_id = MVP_ROOM_ID
    return room_id


RequireInRoom = Depends(get_current_room_id)
CurrentRoomId = Annotated[RoomId, Depends(get_current_room_id)]
