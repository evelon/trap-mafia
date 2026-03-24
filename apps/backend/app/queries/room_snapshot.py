from __future__ import annotations

from uuid import UUID

from app.core.exceptions import raise_not_found
from app.domain.events.room import RoomSnapshotType
from app.repositories.case import CaseRepo
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.schemas.common.error import NotFoundErrorCode
from app.schemas.room.state import (
    RoomCaseInfo,
    RoomInfo,
    RoomMember,
    RoomSettings,
    RoomSnapshot,
)


class RoomSnapshotQuery:
    def __init__(
        self,
        *,
        room_repo: RoomRepo,
        room_member_repo: RoomMemberRepo,
        case_repo: CaseRepo,
    ) -> None:
        self._room_repo = room_repo
        self._room_member_repo = room_member_repo
        self._case_repo = case_repo

    async def build_snapshot(
        self,
        *,
        room_id: UUID,
        last_event: RoomSnapshotType,
        logs: list[str],
    ) -> RoomSnapshot:
        room = await self._room_repo.get_by_id(room_id=room_id)
        if room is None:
            raise_not_found(code=NotFoundErrorCode.NOT_FOUND_ROOM)

        members_rows = await self._room_member_repo.get_active_members_by_room_id(room_id=room_id)
        members = [
            RoomMember(
                user_id=m.user_id,
                username=m.username,
                joined_at=m.joined_at.isoformat(),
            )
            for m in members_rows
        ]

        running_case = await self._case_repo.get_running_by_room_id(room_id=room_id)
        current_case = None
        if running_case is not None:
            current_case = RoomCaseInfo(
                case_id=running_case.id,
                status=running_case.status,
            )

        # MVP: settings는 MVP에선 상수(또는 config에서 로드)
        settings = RoomSettings()

        return RoomSnapshot(
            room=RoomInfo(
                id=room.id,
                room_name=room.name,
                host_user_id=room.host_id,
                created_at=room.created_at.isoformat(),
            ),
            settings=settings,
            current_case=current_case,
            members=members,
            last_event=last_event,
            logs=logs,
        )
