import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseStatus
from app.models.auth import User
from app.models.room import Room, RoomMember
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.room_member import RoomMemberRepo
from app.services.case import CaseService


async def _create_user(db: AsyncSession, username: str) -> User:
    user = User(username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_room_with_members(db: AsyncSession, users: list[User]) -> Room:
    room = Room(name="test_room", host_id=users[0].id)
    db.add(room)
    await db.commit()
    await db.refresh(room)

    members = [RoomMember(user_id=user.id, room_id=room.id) for user in users]
    db.add_all(members)
    await db.commit()
    return room


async def _room_with_members(db: AsyncSession) -> Room:
    usernames = ["username1", "username2", "username3", "username4"]
    users = [await _create_user(db, username) for username in usernames]
    room_with_members = await _create_room_with_members(db, users)
    return room_with_members


@pytest.mark.anyio
async def test_start_case_creates_case_players_and_first_snapshot(
    db_session: AsyncSession,
):
    room_with_members = await _room_with_members(db_session)
    case_repo = CaseRepo(db_session)
    case_player_repo = CasePlayerRepo(db_session)
    case_history_repo = CaseSnapshotHistoryRepo(db_session)
    room_member_repo = RoomMemberRepo(db_session)

    service = CaseService(
        db=db_session,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
    )

    room_id = room_with_members.id

    case = await service.start_case(
        room_id=room_id,
    )

    # case row
    created_case = await case_repo.get_by_id(case_id=case.id)
    assert created_case is not None
    assert created_case.room_id == room_id
    assert created_case.status == CaseStatus.RUNNING
    assert created_case.current_round_no == 1

    # case_players
    players = await case_player_repo.list_by_case_id(case_id=case.id)
    assert len(players) == 4  # 예시
    assert [p.seat_no for p in players] == [0, 1, 2, 3]

    # first snapshot
    latest_snapshot = await case_history_repo.get_latest_by_case_id(case_id=case.id)
    assert latest_snapshot is not None
    assert latest_snapshot.snapshot_no == 1
