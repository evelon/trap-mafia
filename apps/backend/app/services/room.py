from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import DbSessionDep
from app.repositories.room_member import RoomMemberRepo, RoomMemberRepoDep
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import (
    JoinRoomMutation,
    JoinRoomReason,
    LeaveRoomMutation,
    LeaveRoomReason,
)


class RoomService:
    """
    Room 관련 정책/워크플로우.

    규칙:
    - commit/rollback은 여기서 한다. (repo는 순수 DB 접근만)
    """

    def __init__(self, db: AsyncSession, member_repo: RoomMemberRepo | None = None) -> None:
        self.db = db
        self.member_repo = member_repo or RoomMemberRepo(db)

    async def join_room(self, *, user_id: uuid.UUID, room_id: uuid.UUID) -> JoinRoomMutation:
        """
        정책:
        - active membership이 없으면 -> 새로 join
        - active membership이 있고 room_id가 같으면 -> 멱등 (no-op)
        - active membership이 있고 room_id가 다르면 -> 기존 leave 후 새로 join
        """
        active = await self.member_repo.get_active_by_user_id(user_id=user_id)

        if active is not None and active.room_id == room_id:
            # 이미 같은 방에 있음 -> 멱등
            return JoinRoomMutation(
                target=Target.ROOM,
                subject=Subject.ME,
                subject_id=None,
                on_target=True,
                changed=False,
                reason=JoinRoomReason.ALREADY_JOINED,
            )

        # 다른 방에 active가 있으면 먼저 종료
        if active is not None:
            await self.member_repo.leave_active_by_user_id(user_id=user_id)

        # 새 멤버십 생성
        member = await self.member_repo.create_membership(user_id=user_id, room_id=room_id)

        # 트랜잭션 확정
        await self.db.commit()
        # server_default(joined_at) 반영
        await self.db.refresh(member)

        return JoinRoomMutation(
            target=Target.ROOM,
            subject=Subject.ME,
            subject_id=None,
            on_target=True,
            changed=True,
            reason=JoinRoomReason.JOINED,
        )

    async def leave_current_room(self, *, user_id: uuid.UUID) -> LeaveRoomMutation:
        """
        정책:
        - active membership이 있으면 종료 (changed=True)
        - 없으면 멱등 처리 (changed=False)
        """
        updated = await self.member_repo.leave_active_by_user_id(user_id=user_id)
        await self.db.commit()

        if updated == 0:
            return LeaveRoomMutation(
                target=Target.ROOM,
                subject=Subject.ME,
                subject_id=None,
                on_target=False,
                changed=False,
                reason=LeaveRoomReason.ALREADY_LEFT,
            )

        return LeaveRoomMutation(
            target=Target.ROOM,
            subject=Subject.ME,
            subject_id=None,
            on_target=False,
            changed=True,
            reason=LeaveRoomReason.LEFT,
        )


def get_room_service(db: DbSessionDep, repo: RoomMemberRepoDep) -> RoomService:
    return RoomService(db, member_repo=repo)


RoomServiceDep = Annotated[RoomService, Depends(get_room_service)]
