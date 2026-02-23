from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.models.auth import User
from app.models.room import Room, RoomMember
from app.schemas.common.mutation import BaseMutation, Subject, Target
from app.schemas.room.mutation import JoinRoomReason, LeaveRoomReason
from app.services.room import RoomService


async def _create_user(db, *, username: str) -> UUID:
    user = User(id=uuid4(), username=username)
    db.add(user)
    await db.commit()
    return user.id


async def _create_room(db, *, host_id: UUID) -> UUID:
    room = Room(id=uuid4(), host_id=host_id)
    db.add(room)
    await db.commit()
    return room.id


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
@pytest.mark.asyncio
async def test_service_join_room_first_time_and_idempotent(db_session):
    """
    Service 스펙(join):
    - 유저가 방에 없으면:
      - active membership 생성
      - changed=True, reason='joined', on_target=True
    - 이미 같은 방이면:
      - DB 변경 없음
      - changed=False, reason='already_joined', on_target=True
    """
    user_id = await _create_user(db_session, username="svc_user_1")
    room_id = await _create_room(db_session, host_id=user_id)

    svc = RoomService(db_session)

    # first join
    m1 = await svc.join_room(user_id=user_id, room_id=room_id)
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
    m2 = await svc.join_room(user_id=user_id, room_id=room_id)
    assert isinstance(m2, BaseMutation)
    assert m2.target == Target.ROOM
    assert m2.subject == Subject.ME
    assert m2.on_target is True
    assert m2.changed is False
    assert m2.reason == JoinRoomReason.ALREADY_JOINED

    assert await _count_active(db_session, user_id=user_id) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_join_room_switches_active_membership(db_session):
    """
    Service 스펙(join switching):
    - 유저가 room A에 active면
      - room B join 시 A는 left_at 채우고,
      - B가 새로운 active가 된다.
    - 정책: 한 user는 동시에 active membership 1개
    """
    user_id = await _create_user(db_session, username="svc_user_2")
    room_a = await _create_room(db_session, host_id=user_id)
    room_b = await _create_room(db_session, host_id=user_id)

    svc = RoomService(db_session)

    await svc.join_room(user_id=user_id, room_id=room_a)
    assert await _count_active(db_session, user_id=user_id) == 1
    active_a = await _get_active(db_session, user_id=user_id)
    assert active_a is not None
    assert active_a.room_id == room_a

    m = await svc.join_room(user_id=user_id, room_id=room_b)
    assert isinstance(m, BaseMutation)
    assert m.target == Target.ROOM
    assert m.subject == Subject.ME
    assert m.on_target is True
    assert m.changed is True
    assert m.reason == JoinRoomReason.JOINED

    assert await _count_active(db_session, user_id=user_id) == 1
    active_b = await _get_active(db_session, user_id=user_id)
    assert active_b is not None
    assert active_b.room_id == room_b

    # A membership은 종료(left_at not null)
    q = select(RoomMember).where(RoomMember.user_id == user_id, RoomMember.room_id == room_a)
    old = (await db_session.execute(q)).scalar_one()
    assert old.left_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_leave_current_room_idempotent_when_not_in_room(db_session):
    """
    Service 스펙(leave):
    - active membership이 없으면:
      - DB 변경 없음
      - on_target=False
      - changed=False
      - reason=ALREADY_LEFT
    """
    user_id = await _create_user(db_session, username="svc_user_leave_idem")

    svc = RoomService(db_session)

    m = await svc.leave_current_room(user_id=user_id)
    assert isinstance(m, BaseMutation)
    assert m.target == Target.ROOM
    assert m.subject == Subject.ME
    assert m.subject_id is None
    assert m.on_target is False
    assert m.changed is False
    assert m.reason == LeaveRoomReason.ALREADY_LEFT

    assert await _count_active(db_session, user_id=user_id) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_leave_current_room_ends_active_membership(db_session):
    """
    Service 스펙(leave):
    - active membership이 있으면:
      - left_at을 채워서 종료
      - on_target=False
      - changed=True
      - reason=LEFT
    """
    user_id = await _create_user(db_session, username="svc_user_leave_ok")
    room_id = await _create_room(db_session, host_id=user_id)

    svc = RoomService(db_session)

    await svc.join_room(user_id=user_id, room_id=room_id)
    assert await _count_active(db_session, user_id=user_id) == 1

    m = await svc.leave_current_room(user_id=user_id)
    assert isinstance(m, BaseMutation)
    assert m.target == Target.ROOM
    assert m.subject == Subject.ME
    assert m.subject_id is None
    assert m.on_target is False
    assert m.changed is True
    assert m.reason == LeaveRoomReason.LEFT

    assert await _count_active(db_session, user_id=user_id) == 0
