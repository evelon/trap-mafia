from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseStatus
from app.models.auth import User
from app.models.case import Case
from app.models.room import Room
from app.repositories.case import CaseRepo


async def _create_user(
    db_session: AsyncSession,
    *,
    username: str,
) -> User:
    user = User(username=username)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_room(
    db_session: AsyncSession,
    *,
    host_id: UUID,
    room_name: str = "test-room",
) -> Room:
    # MVP
    room = await db_session.get(Room, UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))
    assert room
    return room
    # room = Room(
    #     id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
    #     name=room_name,
    #     host_id=host_id,
    # )
    # db_session.add(room)
    # await db_session.commit()
    # await db_session.refresh(room)
    # return room


async def _create_case_row(
    db_session: AsyncSession,
    *,
    room_id: UUID,
    host_user_id: UUID,
    status: CaseStatus = CaseStatus.RUNNING,
    current_round_no: int = 1,
    ended_at: datetime | None = None,
) -> Case:
    kwargs = {}
    if ended_at is not None:
        kwargs["ended_at"] = ended_at

    row = Case(
        room_id=room_id,
        host_user_id=host_user_id,
        status=status,
        current_round_no=current_round_no,
        **kwargs,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


@pytest.mark.anyio
async def test_create_inserts_case_row(db_session: AsyncSession) -> None:
    repo = CaseRepo(db_session)

    host = await _create_user(db_session, username="host")
    room = await _create_room(db_session, host_id=host.id)

    row = await repo.create(
        room_id=room.id,
        host_user_id=host.id,
        status=CaseStatus.RUNNING,
        current_round_no=1,
    )
    await db_session.commit()

    found = await repo.get_by_id(case_id=row.id)

    assert found is not None
    assert found.id == row.id
    assert found.room_id == room.id
    assert found.host_user_id == host.id
    assert found.status == CaseStatus.RUNNING
    assert found.current_round_no == 1


@pytest.mark.anyio
async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = CaseRepo(db_session)

    found = await repo.get_by_id(case_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

    assert found is None


@pytest.mark.anyio
async def test_get_running_by_room_id_returns_running_case(db_session: AsyncSession) -> None:
    repo = CaseRepo(db_session)

    host = await _create_user(db_session, username="host")
    room = await _create_room(db_session, host_id=host.id)

    running = await _create_case_row(
        db_session,
        room_id=room.id,
        host_user_id=host.id,
        status=CaseStatus.RUNNING,
        current_round_no=2,
    )

    found = await repo.get_running_by_room_id(room_id=room.id)

    assert found is not None
    assert found.id == running.id
    assert found.status == CaseStatus.RUNNING
    assert found.current_round_no == 2


@pytest.mark.anyio
async def test_get_running_by_room_id_returns_none_when_only_ended_case_exists(
    db_session: AsyncSession,
) -> None:
    repo = CaseRepo(db_session)

    host = await _create_user(db_session, username="host")
    room = await _create_room(db_session, host_id=host.id)

    await _create_case_row(
        db_session,
        room_id=room.id,
        host_user_id=host.id,
        status=CaseStatus.ENDED,
        current_round_no=3,
        ended_at=datetime.now(timezone.utc),
    )

    found = await repo.get_running_by_room_id(room_id=room.id)

    assert found is None
