from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.models.room import RoomMember

# 네가 만들 repo
from app.repositories.room_member import RoomMemberRepo
from tests._helpers.entity import create_room, create_user


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


# Helper to count rows for a given (user_id, room_id) in RoomMember
async def _count_room_user_rows(db, *, user_id: uuid.UUID, room_id: uuid.UUID) -> int:
    q = (
        select(func.count())
        .select_from(RoomMember)
        .where(RoomMember.user_id == user_id, RoomMember.room_id == room_id)
    )
    return int((await db.execute(q)).scalar_one())


# MVP: MVP does not use `repo.create_membership`.
@pytest.mark.unit
async def test_repo_create_membership_creates_active_row(db_session):
    """
    Repo 스펙:
    - create_membership(user_id, room_id)는 room_members에 row를 만든다.
    - active 정의: left_at IS NULL
    """
    user_id = await create_user(db_session, username="repo_user_1")
    room_id = await create_room(db_session, host_id=user_id)

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
async def test_repo_leave_active_sets_left_at(db_session):
    """
    Repo 스펙:
    - leave_active_by_user_id(user_id)는 active membership(있으면)을 종료시킨다.
    - 결과적으로 active count는 0이 된다.
    """
    user_id = await create_user(db_session, username="repo_user_2")
    room_id = await create_room(db_session, host_id=user_id)

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
async def test_repo_get_active_returns_none_when_no_active(db_session):
    """
    Repo 스펙:
    - get_active_by_user_id(user_id)는 active가 없으면 None을 반환한다.
    """
    user_id = await create_user(db_session, username="repo_user_3")
    repo = RoomMemberRepo(db_session)

    active = await repo.get_active_by_user_id(user_id=user_id)
    assert active is None


@pytest.mark.unit
async def test_repo_leave_active_returns_zero_when_no_active(db_session):
    """
    Repo 스펙:
    - active membership이 없으면 leave_active_by_user_id는 0(rowcount)을 반환한다.
    - 예외를 던지지 않는다.
    """
    user_id = await create_user(db_session, username="repo_user_leave_none")

    repo = RoomMemberRepo(db_session)
    left_member = await repo.leave_active_by_user_id(user_id=user_id)

    assert left_member is None
    assert await _count_active(db_session, user_id=user_id) == 0


# --- upsert (revive) tests ---


@pytest.mark.unit
async def test_repo_upsert_membership_inserts_when_missing(db_session):
    """
    Repo 스펙(upsert):
    - upsert_membership(user_id, room_id)
      - row가 없으면 INSERT
      - 결과 row는 active(left_at IS NULL)
    """
    user_id = await create_user(db_session, username="repo_upsert_user_1")
    room_id = await create_room(db_session, host_id=user_id)

    repo = RoomMemberRepo(db_session)

    m = await repo.upsert_membership(user_id=user_id, room_id=room_id)
    await db_session.commit()

    assert m.user_id == user_id
    assert m.room_id == room_id
    assert m.left_at is None

    assert await _count_room_user_rows(db_session, user_id=user_id, room_id=room_id) == 1
    assert await _count_active(db_session, user_id=user_id) == 1


@pytest.mark.unit
async def test_repo_upsert_membership_revives_when_left(db_session):
    """
    Repo 스펙(upsert revive):
    - (room_id, user_id) row가 이미 있고 left_at != NULL이면
      - upsert_membership은 INSERT를 하지 않고
      - left_at을 NULL로 만들어 revive 한다.
    """
    user_id = await create_user(db_session, username="repo_upsert_user_2")
    room_id = await create_room(db_session, host_id=user_id)

    repo = RoomMemberRepo(db_session)

    # 최초 가입
    m1 = await repo.upsert_membership(user_id=user_id, room_id=room_id)
    await db_session.commit()

    assert m1.left_at is None
    assert await _count_room_user_rows(db_session, user_id=user_id, room_id=room_id) == 1
    assert await _count_active(db_session, user_id=user_id) == 1

    # 나가기(종료)
    updated = await repo.leave_active_by_user_id(user_id=user_id)
    # 구현 선택지에 따라 0/1/bool/row 등을 반환할 수 있으니, 종료 자체가 된 것만 확인
    assert updated is not None
    await db_session.commit()

    assert await _count_active(db_session, user_id=user_id) == 0

    # revive
    m2 = await repo.upsert_membership(user_id=user_id, room_id=room_id)
    await db_session.commit()

    assert m2.user_id == user_id
    assert m2.room_id == room_id
    assert m2.left_at is None

    # 복합 PK이므로 row 수는 여전히 1이어야 함
    assert await _count_room_user_rows(db_session, user_id=user_id, room_id=room_id) == 1
    assert await _count_active(db_session, user_id=user_id) == 1
