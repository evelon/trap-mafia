from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import DbSessionDep
from app.mvp import MVP_ROOM_ID
from app.repositories.room_member import RoomMemberRepo, RoomMemberRepoDep
from app.repositories.user import UserRepo, UserRepoDep
from app.schemas.common.ids import RoomId, UserId
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import (
    JoinRoomMutation,
    JoinRoomReason,
    KickUserMutation,
    KickUserReason,
    LeaveRoomMutation,
    LeaveRoomReason,
)


class RoomService:
    """
    Room 관련 정책/워크플로우.

    규칙:
    - commit/rollback은 여기서 한다. (repo는 순수 DB 접근만)
    """

    def __init__(
        self,
        db: AsyncSession,
        member_repo: RoomMemberRepo | None = None,
        user_repo: UserRepo | None = None,
    ) -> None:
        self.db = db
        self.member_repo = member_repo or RoomMemberRepo(db)
        self.user_repo = user_repo or UserRepo(db)

    def _normalize_room_id(self, requested_room_id: RoomId) -> RoomId:
        return MVP_ROOM_ID

    async def join_room(self, *, user_id: UserId, room_id: RoomId) -> JoinRoomMutation:
        """
        정책:
        - active membership이 없으면 -> 새로 join
        - active membership이 있고 room_id가 같으면 -> 멱등 (no-op)
        - active membership이 있고 room_id가 다르면 -> 기존 leave 후 새로 join
        """
        room_id = self._normalize_room_id(room_id)  # MVP
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
        member = await self.member_repo.upsert_membership(user_id=user_id, room_id=room_id)

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

    async def leave_current_room(self, *, user_id: UserId) -> LeaveRoomMutation:
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

    async def kick_user(
        self,
        *,
        actor_user_id: UserId,
        target_user_id: UserId,
    ) -> KickUserMutation:
        """
        정책 (MVP):
        - 누구나 누구나 kick 가능 (권한 체크 없음)
        - target이 현재 room에 없으면 멱등 처리
        - DB 효과는 leave와 동일 (left_at 채움)
        """

        # 1. target user 존재 확인 (없으면 EntityNotFoundError)
        await self.user_repo.ensure_exists(target_user_id)

        # 2. target의 active membership 조회
        active = await self.member_repo.get_active_by_user_id(user_id=target_user_id)

        # 3. 방에 없는 경우 (멱등)
        if active is None:
            return KickUserMutation(
                subject_id=target_user_id,
                changed=False,
                reason=KickUserReason.NOT_IN_ROOM,
            )

        # 4. 실제 kick (leave와 동일한 DB 변경)
        await self.member_repo.leave_active_by_user_id(user_id=target_user_id)

        await self.db.commit()

        return KickUserMutation(
            subject_id=target_user_id,
            changed=True,
            reason=KickUserReason.KICKED,
        )


def get_room_service(
    db: DbSessionDep,
    repo: RoomMemberRepoDep,
    user_repo: UserRepoDep,
) -> RoomService:
    return RoomService(db, member_repo=repo, user_repo=user_repo)


RoomServiceDep = Annotated[RoomService, Depends(get_room_service)]
