from __future__ import annotations

import uuid
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.exceptions.common import EntityNotFoundError
from app.models.room import RoomMember
from app.mvp import MVP_ROOM_ID
from app.schemas.common.mutation import BaseMutation, Subject, Target
from app.schemas.room.mutation import JoinRoomReason, KickUserReason, LeaveRoomReason
from app.services.room import RoomService
from tests._helpers.entity import create_room, create_user


async def _count_active(db, *, user_id: UUID) -> int:
    q = (
        select(func.count())
        .select_from(RoomMember)
        .where(
            RoomMember.user_id == user_id,
            RoomMember.left_at.is_(None),
        )
    )
    return int((await db.execute(q)).scalar_one())


async def _get_active(db, *, user_id: UUID) -> RoomMember | None:
    q = select(RoomMember).where(
        RoomMember.user_id == user_id,
        RoomMember.left_at.is_(None),
    )
    return (await db.execute(q)).scalar_one_or_none()


@pytest.mark.unit
async def test_service_join_room_first_time_and_idempotent(
    db_session, client, room_service: RoomService
):
    """
    Service 스펙(join):
    - 유저가 방에 없으면:
      - active membership 생성
      - changed=True, reason='joined', on_target=True
    - 이미 같은 방이면:
      - DB 변경 없음
      - changed=False, reason='already_joined', on_target=True
    """
    user_id = await create_user(db_session, username="svc_user_1")
    room_id = await create_room(db_session, host_id=user_id)

    # first join
    m1 = await room_service.join_room(user_id=user_id, room_id=room_id)
    assert isinstance(m1, BaseMutation)
    assert m1.target == Target.ROOM
    assert m1.subject == Subject.ME
    assert m1.on_target is True
    assert m1.changed is True
    assert m1.reason == JoinRoomReason.JOINED

    assert await _count_active(db_session, user_id=user_id) == 1
    active = await _get_active(db_session, user_id=user_id)
    assert active is not None
    assert active.room_id == room_id

    # second join (same room) -> idempotent
    m2 = await room_service.join_room(user_id=user_id, room_id=room_id)
    assert isinstance(m2, BaseMutation)
    assert m2.target == Target.ROOM
    assert m2.subject == Subject.ME
    assert m2.on_target is True
    assert m2.changed is False
    assert m2.reason == JoinRoomReason.ALREADY_JOINED

    assert await _count_active(db_session, user_id=user_id) == 1


# MVP: This test is not working on MVP
# @pytest.mark.unit
# @pytest.mark.asyncio
# async def test_service_join_room_switches_active_membership(db_session):
#     """
#     Service 스펙(join switching):
#     - 유저가 room A에 active면
#       - room B join 시 A는 left_at 채우고,
#       - B가 새로운 active가 된다.
#     - 정책: 한 user는 동시에 active membership 1개
#     """
#     user_id = await create_user(db_session, username="svc_user_2")
#     room_a = await create_room(db_session, host_id=user_id)
#     room_b = await create_room(db_session, host_id=user_id)

#     svc = RoomService(db_session)

#     await svc.join_room(user_id=user_id, room_id=room_a)
#     assert await _count_active(db_session, user_id=user_id) == 1
#     active_a = await _get_active(db_session, user_id=user_id)
#     assert active_a is not None
#     assert active_a.room_id == room_a

#     m = await svc.join_room(user_id=user_id, room_id=room_b)
#     assert isinstance(m, BaseMutation)
#     assert m.target == Target.ROOM
#     assert m.subject == Subject.ME
#     assert m.on_target is True
#     assert m.changed is True
#     assert m.reason == JoinRoomReason.JOINED

#     assert await _count_active(db_session, user_id=user_id) == 1
#     active_b = await _get_active(db_session, user_id=user_id)
#     assert active_b is not None
#     assert active_b.room_id == room_b

#     # A membership은 종료(left_at not null)
#     q = select(RoomMember).where(RoomMember.user_id == user_id, RoomMember.room_id == room_a)
#     old = (await db_session.execute(q)).scalar_one()
#     assert old.left_at is not None


@pytest.mark.unit
async def test_service_leave_current_room_idempotent_when_not_in_room(
    db_session, room_service: RoomService
):
    """
    Service 스펙(leave):
    - active membership이 없으면:
      - DB 변경 없음
      - on_target=False
      - changed=False
      - reason=ALREADY_LEFT
    """
    user_id = await create_user(db_session, username="svc_user_leave_idem")

    m = await room_service.leave_room(user_id=user_id)
    assert isinstance(m, BaseMutation)
    assert m.target == Target.ROOM
    assert m.subject == Subject.ME
    assert m.subject_id is None
    assert m.on_target is False
    assert m.changed is False
    assert m.reason == LeaveRoomReason.ALREADY_LEFT

    assert await _count_active(db_session, user_id=user_id) == 0


@pytest.mark.unit
async def test_service_leave_current_room_ends_active_membership(
    db_session, room_service: RoomService
):
    """
    Service 스펙(leave):
    - active membership이 있으면:
      - left_at을 채워서 종료
      - on_target=False
      - changed=True
      - reason=LEFT
    """
    user_id = await create_user(db_session, username="svc_user_leave_ok")
    room_id = await create_room(db_session, host_id=user_id)

    await room_service.join_room(user_id=user_id, room_id=room_id)
    assert await _count_active(db_session, user_id=user_id) == 1

    m = await room_service.leave_room(user_id=user_id)
    assert isinstance(m, BaseMutation)
    assert m.target == Target.ROOM
    assert m.subject == Subject.ME
    assert m.subject_id is None
    assert m.on_target is False
    assert m.changed is True
    assert m.reason == LeaveRoomReason.LEFT

    assert await _count_active(db_session, user_id=user_id) == 0


@pytest.mark.unit
async def test_service_kick_user_success(db_session, room_service: RoomService):
    """
    - 대상이 방에 있으면
      - left_at 채워짐
      - changed=True
      - reason=KICKED
    """
    user_a = await create_user(db_session, username="svc_kick_a")
    user_b = await create_user(db_session, username="svc_kick_b")

    room_id = await create_room(db_session, host_id=user_a)

    # B를 room에 join
    await room_service.join_room(user_id=user_b, room_id=room_id)
    assert await _count_active(db_session, user_id=user_b) == 1

    # A가 B를 kick
    m = await room_service.kick_user(
        actor_user_id=user_a,
        room_id=room_id,
        target_user_id=user_b,
    )

    assert m.target == Target.ROOM
    assert m.subject == Subject.USER
    assert m.subject_id == user_b
    assert m.on_target is False
    assert m.changed is True
    assert m.reason == KickUserReason.KICKED

    assert await _count_active(db_session, user_id=user_b) == 0


@pytest.mark.unit
async def test_service_kick_user_idempotent_when_not_in_room(
    db_session: AsyncSession, room_service: RoomService
):
    """
    - 대상이 방에 없으면
      - changed=False
      - reason=NOT_IN_ROOM
    """
    username_a = "svc_kick2_a"
    username_b = "svc_kick2_b"
    user_a = await create_user(db_session, username=username_a)
    user_b = await create_user(db_session, username=username_b)
    room_id = await create_room(db_session, host_id=user_a)

    m = await room_service.kick_user(
        actor_user_id=user_a,
        room_id=room_id,
        target_user_id=user_b,
    )

    assert m.target == Target.ROOM
    assert m.subject == Subject.USER
    assert m.subject_id == user_b
    assert m.on_target is False
    assert m.changed is False
    assert m.reason == KickUserReason.NOT_IN_ROOM


@pytest.mark.unit
async def test_service_join_room_normalizes_to_mvp_room(db_session, room_service: RoomService):
    """
    MVP 정책:
    - 어떤 room_id를 요청하더라도 실제 membership은 MVP_ROOM_ID로 생성된다.
    - 즉, service는 room_id를 내부적으로 정규화한다.
    """

    user_id = await create_user(db_session, username="svc_user_mvp_norm")

    # 일부러 다른 UUID를 넘긴다
    random_room_id = uuid4()

    m = await room_service.join_room(user_id=user_id, room_id=random_room_id)

    assert m.reason == JoinRoomReason.JOINED
    assert m.changed is True

    # 실제 active membership 확인
    active = await _get_active(db_session, user_id=user_id)
    assert active is not None

    # 핵심 검증: random_room_id가 아니라 MVP_ROOM_ID여야 한다
    assert active.room_id == MVP_ROOM_ID


@pytest.mark.unit
async def test_service_kick_user_raises_when_target_user_missing(
    db_session, room_service: RoomService
):
    """
    계약:
    - target_user_id가 존재하지 않으면 예외를 던진다.
    - NOT_IN_ROOM 멱등으로 처리하지 않는다.
    """
    room_id = MVP_ROOM_ID

    actor_id = uuid.uuid4()
    missing_target_id = uuid.uuid4()

    # 너희 프로젝트의 NotFound 예외 타입으로 바꿔줘.
    # 예: DomainError, AppException, NotFoundError 등
    with pytest.raises(EntityNotFoundError):
        await room_service.kick_user(
            actor_user_id=actor_id, room_id=room_id, target_user_id=missing_target_id
        )
