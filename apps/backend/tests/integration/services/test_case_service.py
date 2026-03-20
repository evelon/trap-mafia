import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseStatus, PhaseType
from app.models.auth import User
from app.models.case_snapshot import CaseSnapshotHistory
from app.models.room import Room, RoomMember
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.schemas.case.state import CaseSnapshot
from app.services.case import CaseService
from tests._helpers.entity import room_with_members


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


@pytest.mark.anyio
async def test_start_case_creates_case_and_players(
    db_session: AsyncSession,
):
    room, _ = await room_with_members(db_session)
    case_repo = CaseRepo(db_session)
    case_player_repo = CasePlayerRepo(db_session)
    case_history_repo = CaseSnapshotHistoryRepo(db_session)
    room_member_repo = RoomMemberRepo(db_session)
    room_repo = RoomRepo(db_session)

    service = CaseService(
        db=db_session,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
        room_repo=room_repo,
    )

    room_id = room.id

    case = await service.start_case(
        room_id=room_id,
    )
    await db_session.flush()

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


@pytest.mark.anyio
async def test_start_case_creates_first_snapshot(
    db_session: AsyncSession,
):
    room, _ = await room_with_members(db_session)
    case_repo = CaseRepo(db_session)
    case_player_repo = CasePlayerRepo(db_session)
    case_history_repo = CaseSnapshotHistoryRepo(db_session)
    room_member_repo = RoomMemberRepo(db_session)
    room_repo = RoomRepo(db_session)

    service = CaseService(
        db=db_session,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
        room_repo=room_repo,
    )

    room_id = room.id

    case = await service.start_case(
        room_id=room_id,
    )

    latest_snapshot = await case_history_repo.get_latest_by_case_id(case_id=case.id)
    assert latest_snapshot is not None


@pytest.mark.anyio
async def test_start_case_creates_first_snapshot_in_case_snapshot_shape(
    db_session: AsyncSession,
):
    room, _ = await room_with_members(db_session)
    case_repo = CaseRepo(db_session)
    case_player_repo = CasePlayerRepo(db_session)
    case_history_repo = CaseSnapshotHistoryRepo(db_session)
    room_member_repo = RoomMemberRepo(db_session)
    room_repo = RoomRepo(db_session)

    service = CaseService(
        db=db_session,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
        room_repo=room_repo,
    )

    case = await service.start_case(
        room_id=room.id,
    )

    latest_snapshot = await case_history_repo.get_latest_by_case_id(case_id=case.id)
    assert latest_snapshot is not None

    snapshot = CaseSnapshot.model_validate(latest_snapshot.snapshot_json)

    assert snapshot.schema_version == 1
    assert snapshot.case_state.case_id == case.id
    assert snapshot.case_state.status == CaseStatus.RUNNING
    assert snapshot.case_state.round_no == 1

    assert len(snapshot.players) == 4
    assert {p.username for p in snapshot.players} == {
        "username1",
        "username2",
        "username3",
        "username4",
    }
    assert [p.seat_no for p in snapshot.players] == [0, 1, 2, 3]
    assert [p.life_left for p in snapshot.players] == [2, 2, 2, 2]
    assert [p.vote_tokens for p in snapshot.players] == [0, 0, 0, 0]

    assert snapshot.logs == []


@pytest.mark.anyio
async def test_start_case_snapshot_matches_schema(
    db_session: AsyncSession,
):
    case_repo = CaseRepo(db_session)
    case_player_repo = CasePlayerRepo(db_session)
    case_history_repo = CaseSnapshotHistoryRepo(db_session)
    room_member_repo = RoomMemberRepo(db_session)
    room_repo = RoomRepo(db_session)

    case_service = CaseService(
        db=db_session,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
        room_repo=room_repo,
    )

    # given
    room, users = await room_with_members(db_session)

    # when
    await case_service.start_case(room_id=room.id)

    # then

    result = await db_session.execute(
        select(CaseSnapshotHistory).order_by(CaseSnapshotHistory.snapshot_no.asc())
    )
    snapshot = result.scalars().first()

    assert snapshot is not None

    # 🔥 핵심: schema validation
    validated = CaseSnapshot.model_validate(snapshot.snapshot_json)

    # --- 기본 필드 ---
    assert validated.schema_version == 1
    assert validated.case_state.status == CaseStatus.RUNNING
    assert validated.case_state.round_no == 1

    # --- players ---
    assert len(validated.players) == len(users)

    # seat_no 순서 보장 확인
    seat_nos = [p.seat_no for p in validated.players]
    assert seat_nos == sorted(seat_nos)

    # username 존재 확인
    usernames = [p.username for p in validated.players]
    expected_usernames = [u.username for u in users]
    assert set(usernames) == set(expected_usernames)

    # --- phase ---
    assert validated.phase_state.phase_type == PhaseType.NIGHT
    assert validated.phase_state.history_id >= 1

    # --- logs ---
    assert isinstance(validated.logs, list)
    assert all(isinstance(log, str) for log in validated.logs)
