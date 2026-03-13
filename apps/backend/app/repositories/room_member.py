from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.room import RoomMember
from app.repositories.projections import SnapshotRoomMember


class RoomMemberRepo:
    """
    room_members 테이블에 대한 DB 접근 전용 레포.

    규칙:
    - commit/rollback은 하지 않는다. (서비스가 트랜잭션 경계를 책임)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert_membership(self, *, room_id: UUID, user_id: UUID) -> RoomMember:
        """
        (room_id, user_id) 복합 PK 설계에 맞춘 join 처리.

        - row가 없으면: INSERT
        - row가 있는데 left_at != NULL이면: revive (left_at=NULL, joined_at=now)
        - row가 있는데 left_at IS NULL이면: 그대로 반환 (idempotent)
        """
        q = select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
        member = (await self.db.execute(q)).scalar_one_or_none()

        if member is None:
            member = RoomMember(room_id=room_id, user_id=user_id)
            self.db.add(member)
            # commit/flush는 service가 책임지는 패턴이면 여기서 하지 않음
            return member

        # 이미 active면 그대로
        if member.left_at is None:
            return member

        # revive
        member.left_at = None
        member.joined_at = datetime.now(timezone.utc)
        return member

    async def get_active_by_user_id(self, *, user_id: UUID) -> RoomMember | None:
        q = select(RoomMember).where(
            RoomMember.user_id == user_id,
            RoomMember.left_at.is_(None),
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def leave_active_by_user_id(self, *, user_id: UUID) -> bool:
        """
        active membership을 종료(left_at 세팅).
        - 변경이 있으면 True, 없으면 False
        """
        active = await self.get_active_by_user_id(user_id=user_id)
        if active is None:
            return False
        active.left_at = datetime.now(timezone.utc)
        return True

    async def create_membership(self, *, user_id: UUID, room_id: UUID) -> RoomMember:
        member = RoomMember(user_id=user_id, room_id=room_id)
        self.db.add(member)
        # joined_at은 server_default이므로 flush 후 refresh를 서비스에서 해도 되고,
        # 여기서 flush만 해도 된다.
        await self.db.flush()
        return member

    async def get_active_members_by_room_id(self, *, room_id: UUID) -> list[SnapshotRoomMember]:
        q = (
            select(RoomMember.user_id, User.username, RoomMember.joined_at)
            .join(User, User.id == RoomMember.user_id)
            .where(RoomMember.room_id == room_id, RoomMember.left_at.is_(None))
            .order_by(RoomMember.joined_at.asc())
        )
        rows = await self.db.execute(q)

        return [
            SnapshotRoomMember(user_id, username, joined_at)
            for user_id, username, joined_at in rows.tuples().all()
        ]
