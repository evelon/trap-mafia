from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.models.auth import User
from app.models.room import Room, RoomMember

# 네가 만들 repo
from app.repositories.room_member import RoomMemberRepo


async def _create_user(db, *, username: str) -> uuid.UUID:
    user = User(id=uuid.uuid4(), username=username)
    db.add(user)
    await db.commit()
    return user.id


async def _create_room(db, *, host_id: uuid.UUID) -> uuid.UUID:
    room = Room(id=uuid.uuid4(), host_id=host_id)
    db.add(room)
    await db.commit()
    return room.id


async def _count_active(db, *, user_id: uuid.UUID) -> int:
    q = (
        select(func.count())
        .select_from(RoomMember)
        .where(
            RoomMember.user_id == user_id,
            RoomMember.left_at.is_(None),
        )
    )
    return int((await db.execute(q)).scalar_one())


async def _get_active(db, *, user_id: uuid.UUID) -> RoomMember | None:
    q = select(RoomMember).where(
        RoomMember.user_id == user_id,
        RoomMember.left_at.is_(None),
    )
    return (await db.execute(q)).scalar_one_or_none()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_repo_create_membership_creates_active_row(db_session):
    """
    Repo 스펙:
    - create_membership(user_id, room_id)는 room_members에 row를 만든다.
    - active 정의: left_at IS NULL
    """
    user_id = await _create_user(db_session, username="repo_user_1")
    room_id = await _create_room(db_session, host_id=user_id)

    repo = RoomMemberRepo(db_session)
    m = await repo.create_membership(user_id=user_id, room_id=room_id)

    assert m.user_id == user_id
    assert m.room_id == room_id
    assert m.left_at is None

    assert await _count_active(db_session, user_id=user_id) == 1
    active = await _get_active(db_session, user_id=user_id)
    assert active is not None
    assert active.room_id == room_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_repo_leave_active_sets_left_at(db_session):
    """
    Repo 스펙:
    - leave_active_by_user_id(user_id)는 active membership(있으면)을 종료시킨다.
    - 결과적으로 active count는 0이 된다.
    """
    user_id = await _create_user(db_session, username="repo_user_2")
    room_id = await _create_room(db_session, host_id=user_id)

    repo = RoomMemberRepo(db_session)
    await repo.create_membership(user_id=user_id, room_id=room_id)
    assert await _count_active(db_session, user_id=user_id) == 1

    result = await repo.leave_active_by_user_id(user_id=user_id)
    # 구현 선택지: bool / updated membership / rowcount 등
    assert result is not None

    active = await _get_active(db_session, user_id=user_id)
    assert active is None
    assert await _count_active(db_session, user_id=user_id) == 0

    # left_at이 실제로 채워졌는지(최근 row 하나를 조회)
    q = (
        select(RoomMember)
        .where(RoomMember.user_id == user_id)
        .order_by(RoomMember.joined_at.desc())
        .limit(1)
    )
    latest = (await db_session.execute(q)).scalar_one()
    assert latest.left_at is not None
    assert isinstance(latest.left_at, datetime)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_repo_get_active_returns_none_when_no_active(db_session):
    """
    Repo 스펙:
    - get_active_by_user_id(user_id)는 active가 없으면 None을 반환한다.
    """
    user_id = await _create_user(db_session, username="repo_user_3")
    repo = RoomMemberRepo(db_session)

    active = await repo.get_active_by_user_id(user_id=user_id)
    assert active is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_repo_leave_active_returns_zero_when_no_active(db_session):
    """
    Repo 스펙:
    - active membership이 없으면 leave_active_by_user_id는 0(rowcount)을 반환한다.
    - 예외를 던지지 않는다.
    """
    user_id = await _create_user(db_session, username="repo_user_leave_none")

    repo = RoomMemberRepo(db_session)
    updated = await repo.leave_active_by_user_id(user_id=user_id)

    assert updated == 0
    assert await _count_active(db_session, user_id=user_id) == 0
