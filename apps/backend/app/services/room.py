from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import RoomEventDelta, RoomSnapshotType
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.pubsub.topics import RoomTopic
from app.mvp import MVP_ROOM_ID
from app.repositories.room_member import RoomMemberRepo
from app.repositories.user import UserRepo
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
        member_repo: RoomMemberRepo,
        user_repo: UserRepo,
        room_event_bus: RoomEventBus,
    ) -> None:
        self._db = db
        self._member_repo = member_repo
        self._user_repo = user_repo
        self._room_event_bus = room_event_bus

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
        active = await self._member_repo.get_active_by_user_id(user_id=user_id)

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
            await self._member_repo.leave_active_by_user_id(user_id=user_id)

        # 새 멤버십 생성
        member = await self._member_repo.upsert_membership(user_id=user_id, room_id=room_id)

        # 트랜잭션 확정
        await self._db.commit()
        # server_default(joined_at) 반영
        await self._db.refresh(member)
        # Redis pubsub에는 snapshot이 아니라 event delta만 publish한다.
        # 이미 가입된 상태(ALREADY_JOINED)처럼 상태 변화가 없는 경우에는 emit하지 않는다.
        try:
            await self._room_event_bus.publish(
                RoomTopic(room_id),
                RoomEventDelta(
                    type=RoomSnapshotType.MEMBER_JOINED,
                    user_id=user_id,
                ),  # type: ignore[call-arg] # pyright: ignore[reportCallIssue]
            )
        except Exception:
            # MVP: join 응답 자체는 성공시켜야 하므로 event emit 실패는 삼킨다.
            # (원하면 추후 로깅/리트라이/에러 정책으로 강화)
            pass
        return JoinRoomMutation(
            target=Target.ROOM,
            subject=Subject.ME,
            subject_id=None,
            on_target=True,
            changed=True,
            reason=JoinRoomReason.JOINED,
        )

    async def leave_room(self, *, user_id: UserId) -> LeaveRoomMutation:
        """
        정책:
        - active membership이 있으면 종료 (changed=True)
        - 없으면 멱등 처리 (changed=False)
        """
        left_member = await self._member_repo.leave_active_by_user_id(user_id=user_id)
        await self._db.commit()

        if left_member is None:
            return LeaveRoomMutation(
                target=Target.ROOM,
                subject=Subject.ME,
                subject_id=None,
                on_target=False,
                changed=False,
                reason=LeaveRoomReason.ALREADY_LEFT,
            )

        try:
            await self._room_event_bus.publish(
                RoomTopic(left_member.room_id),
                RoomEventDelta(
                    type=RoomSnapshotType.MEMBER_LEFT,
                    user_id=user_id,
                ),  # type: ignore[call-arg] # pyright: ignore[reportCallIssue]
            )
        except Exception:
            # MVP: join 응답 자체는 성공시켜야 하므로 event emit 실패는 삼킨다.
            # (원하면 추후 로깅/리트라이/에러 정책으로 강화)
            pass
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
        await self._user_repo.ensure_exists(target_user_id)

        # 2. target의 active membership 조회
        active = await self._member_repo.get_active_by_user_id(user_id=target_user_id)

        # 3. 방에 없는 경우 (멱등)
        if active is None:
            return KickUserMutation(
                subject_id=target_user_id,
                changed=False,
                reason=KickUserReason.NOT_IN_ROOM,
            )

        # 4. 실제 kick (leave와 동일한 DB 변경)
        await self._member_repo.leave_active_by_user_id(user_id=target_user_id)

        await self._db.commit()

        return KickUserMutation(
            subject_id=target_user_id,
            changed=True,
            reason=KickUserReason.KICKED,
        )
