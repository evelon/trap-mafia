from typing import Awaitable, Callable

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseStatus, PhaseType
from app.models.auth import User
from app.models.case_snapshot import CaseSnapshotHistory
from app.models.room import Room
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.schemas.case.state import CaseSnapshot
from app.services.case import CaseService
from tests._helpers.entity import room_with_members


@pytest.mark.anyio
async def test_start_case_creates_case_and_players(
    db_session: AsyncSession,
    case_repo: CaseRepo,
    case_player_repo: CasePlayerRepo,
    case_service: CaseService,
    user_hosted_room: Room,
    add_new_user_to_room: Callable[[Room], Awaitable[User]],
):
    # given
    room_id = user_hosted_room.id
    for _ in range(3):
        await add_new_user_to_room(user_hosted_room)

    # when
    case_mut = await case_service.start_case(
        room_id=room_id,
    )
    await db_session.flush()

    # then
    case_id = case_mut.subject_id

    # case row
    created_case = await case_repo.get_by_id(case_id=case_id)
    assert created_case is not None
    assert created_case.room_id == room_id
    assert created_case.status == CaseStatus.RUNNING
    assert created_case.current_round_no == 1

    # case_players
    players = await case_player_repo.list_by_case_id(case_id=case_id)
    assert len(players) == 4  # 예시
    assert [p.seat_no for p in players] == [0, 1, 2, 3]


@pytest.mark.anyio
async def test_start_case_creates_first_snapshot(
    case_service: CaseService,
    user_hosted_room: Room,
    add_new_user_to_room: Callable[[Room], Awaitable[User]],
    case_history_repo: CaseSnapshotHistoryRepo,
):
    # given
    room_id = user_hosted_room.id
    for _ in range(3):
        await add_new_user_to_room(user_hosted_room)

    # when
    case_mut = await case_service.start_case(
        room_id=room_id,
    )

    # then
    latest_snapshot = await case_history_repo.get_latest_by_case_id(case_id=case_mut.subject_id)
    assert latest_snapshot is not None


@pytest.mark.anyio
async def test_start_case_creates_first_snapshot_in_case_snapshot_shape(
    case_service: CaseService,
    user_hosted_room: Room,
    add_new_user_to_room: Callable[[Room], Awaitable[User]],
    case_history_repo: CaseSnapshotHistoryRepo,
):
    # given
    room_id = user_hosted_room.id
    user_ids = [user_hosted_room.host_id]
    for _ in range(3):
        user = await add_new_user_to_room(user_hosted_room)
        user_ids.append(user.id)

    # when
    case_mut = await case_service.start_case(
        room_id=room_id,
    )

    # then
    latest_snapshot = await case_history_repo.get_latest_by_case_id(case_id=case_mut.subject_id)
    assert latest_snapshot is not None

    snapshot = CaseSnapshot.model_validate(latest_snapshot.snapshot_json)

    assert snapshot.schema_version == 1
    assert snapshot.case_state.case_id == case_mut.subject_id
    assert snapshot.case_state.status == CaseStatus.RUNNING
    assert snapshot.case_state.round_no == 1

    assert len(snapshot.players) == 4
    assert {p.user_id for p in snapshot.players} == set(user_ids)
    assert [p.seat_no for p in snapshot.players] == [0, 1, 2, 3]
    assert [p.life_left for p in snapshot.players] == [2, 2, 2, 2]
    assert [p.vote_tokens for p in snapshot.players] == [0, 0, 0, 0]

    assert snapshot.logs == []


@pytest.mark.anyio
async def test_start_case_snapshot_matches_schema(
    db_session: AsyncSession, case_service: CaseService
):

    # given
    usernames = ["host_username", "username3", "username4", "username5"]
    room_id, user_ids = await room_with_members(db_session, usernames)

    # when
    await case_service.start_case(room_id=room_id)

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
    assert len(validated.players) == len(user_ids)

    # seat_no 순서 보장 확인
    seat_nos = [p.seat_no for p in validated.players]
    assert seat_nos == sorted(seat_nos)

    # username 존재 확인
    usernames = [p.username for p in validated.players]
    assert set(usernames) == set(usernames)

    # --- phase ---
    assert validated.phase_state.phase_type == PhaseType.NIGHT
    assert validated.phase_state.history_id >= 1

    # --- logs ---
    assert isinstance(validated.logs, list)
    assert all(isinstance(log, str) for log in validated.logs)
