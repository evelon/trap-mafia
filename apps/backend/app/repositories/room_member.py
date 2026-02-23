from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import DbSessionDep
from app.models.room import RoomMember


class RoomMemberRepo:
    """
    room_members 테이블에 대한 DB 접근 전용 레포.

    규칙:
    - commit/rollback은 하지 않는다. (서비스가 트랜잭션 경계를 책임)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_by_user_id(self, *, user_id: UUID) -> RoomMember | None:
        query = select(RoomMember).where(
            RoomMember.user_id == user_id,
            RoomMember.left_at.is_(None),
        )
        return (await self.db.execute(query)).scalar_one_or_none()

    async def create_membership(self, *, user_id: UUID, room_id: UUID) -> RoomMember:
        member = RoomMember(user_id=user_id, room_id=room_id)
        self.db.add(member)
        # joined_at은 server_default이므로 flush 후 refresh를 서비스에서 해도 되고,
        # 여기서 flush만 해도 된다.
        await self.db.flush()
        return member

    async def leave_active_by_user_id(self, *, user_id: UUID) -> int:
        """
        active membership을 종료한다.

        반환:
        - 업데이트된 row 수 (0 or 1)
        """
        query = (
            update(RoomMember)
            .where(RoomMember.user_id == user_id, RoomMember.left_at.is_(None))
            .values(left_at=datetime.now(timezone.utc))
        )
        result = cast(CursorResult, await self.db.execute(query))
        return int(result.rowcount or 0)


def get_room_member_repo(db: DbSessionDep) -> RoomMemberRepo:
    return RoomMemberRepo(db)


RoomMemberRepoDep = Annotated[RoomMemberRepo, Depends(get_room_member_repo)]
