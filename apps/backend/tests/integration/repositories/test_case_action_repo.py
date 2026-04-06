from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import ActionType, PhaseType
from app.models.case import Case, CaseAction, CasePlayer, Phase
from app.repositories.case_action import CaseActionRepo


@pytest.mark.anyio
async def test_create_creates_case_action(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()

    actor = players[0]
    target = players[1]

    # when
    action = await repo.create(
        case_id=case.id,
        phase_id=phase.id,
        actor_player_id=actor.id,
        action_type=ActionType.NIGHT_ACTION_RED_VOTE,
        night_target_seat_no=target.seat_no,
    )
    await db_session.commit()

    # then
    assert action.id is not None
    assert action.case_id == case.id
    assert action.phase_id == phase.id
    assert action.actor_player_id == actor.id
    assert action.action_type == ActionType.NIGHT_ACTION_RED_VOTE
    assert action.night_target_seat_no == target.seat_no
    assert action.is_timeout_auto is False

    result = await db_session.execute(select(CaseAction))
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].id == action.id


@pytest.mark.anyio
async def test_exists_by_phase_and_actor_returns_true_only_for_same_phase_and_actor(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    current_phase = result.scalar_one()

    current_phase.closed_at = current_phase.created_at

    next_phase = Phase(
        case_id=case.id,
        round_no=current_phase.round_no,
        seq_in_round=current_phase.seq_in_round + 1,
        phase_type=PhaseType.DISCUSS,
    )
    db_session.add(next_phase)
    await db_session.flush()

    actor = players[0]
    other_actor = players[1]
    target = players[2]

    await repo.create(
        case_id=case.id,
        phase_id=current_phase.id,
        actor_player_id=actor.id,
        action_type=ActionType.NIGHT_ACTION_RED_VOTE,
        night_target_seat_no=target.seat_no,
    )
    await db_session.commit()

    # when / then
    assert (
        await repo.exists_by_phase_and_actor(
            phase_id=current_phase.id,
            actor_player_id=actor.id,
        )
        is True
    )
    assert (
        await repo.exists_by_phase_and_actor(
            phase_id=current_phase.id,
            actor_player_id=other_actor.id,
        )
        is False
    )
    assert (
        await repo.exists_by_phase_and_actor(
            phase_id=next_phase.id,
            actor_player_id=actor.id,
        )
        is False
    )


@pytest.mark.anyio
async def test_count_by_phase_id_counts_only_actions_in_that_phase(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase1 = result.scalar_one()

    phase1.closed_at = phase1.created_at

    phase2 = Phase(
        case_id=case.id,
        round_no=phase1.round_no,
        seq_in_round=phase1.seq_in_round + 1,
        phase_type=PhaseType.DISCUSS,
    )
    db_session.add(phase2)
    await db_session.flush()

    await repo.create(
        case_id=case.id,
        phase_id=phase1.id,
        actor_player_id=players[0].id,
        action_type=ActionType.NIGHT_ACTION_RED_VOTE,
        night_target_seat_no=players[1].seat_no,
    )
    await repo.create(
        case_id=case.id,
        phase_id=phase1.id,
        actor_player_id=players[1].id,
        action_type=ActionType.NIGHT_ACTION_SKIP,
        night_target_seat_no=None,
    )
    await repo.create(
        case_id=case.id,
        phase_id=phase2.id,
        actor_player_id=players[2].id,
        action_type=ActionType.DISCUSS_ACTION_SKIP,
        night_target_seat_no=None,
    )
    await db_session.commit()

    # when / then
    assert await repo.count_by_phase_id(phase_id=phase1.id) == 2
    assert await repo.count_by_phase_id(phase_id=phase2.id) == 1


@pytest.mark.anyio
async def test_list_by_phase_id_returns_only_actions_in_that_phase(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase1 = result.scalar_one()

    phase1.closed_at = phase1.created_at

    phase2 = Phase(
        case_id=case.id,
        round_no=phase1.round_no,
        seq_in_round=phase1.seq_in_round + 1,
        phase_type=PhaseType.DISCUSS,
    )
    db_session.add(phase2)
    await db_session.flush()

    action1 = await repo.create(
        case_id=case.id,
        phase_id=phase1.id,
        actor_player_id=players[0].id,
        action_type=ActionType.NIGHT_ACTION_RED_VOTE,
        night_target_seat_no=players[1].seat_no,
    )
    action2 = await repo.create(
        case_id=case.id,
        phase_id=phase1.id,
        actor_player_id=players[1].id,
        action_type=ActionType.NIGHT_ACTION_SKIP,
        night_target_seat_no=None,
    )
    await repo.create(
        case_id=case.id,
        phase_id=phase2.id,
        actor_player_id=players[2].id,
        action_type=ActionType.DISCUSS_ACTION_SKIP,
        night_target_seat_no=None,
    )
    await db_session.commit()

    # when
    actions = await repo.list_by_phase_id(phase_id=phase1.id)

    # then
    assert len(actions) == 2
    assert actions[0].id == action1.id
    assert actions[1].id == action2.id
    assert all(action.phase_id == phase1.id for action in actions)


@pytest.mark.anyio
async def test_exists_by_phase_and_actor_returns_false_when_phase_has_no_actions(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()

    # when / then
    assert (
        await repo.exists_by_phase_and_actor(
            phase_id=phase.id,
            actor_player_id=players[0].id,
        )
        is False
    )


@pytest.mark.anyio
async def test_create_sets_created_at(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()

    # when
    action = await repo.create(
        case_id=case.id,
        phase_id=phase.id,
        actor_player_id=players[0].id,
        action_type=ActionType.NIGHT_ACTION_RED_VOTE,
        night_target_seat_no=players[1].seat_no,
    )
    await db_session.commit()

    # then
    assert action.created_at is not None


@pytest.mark.anyio
async def test_create_raises_integrity_error_on_duplicate_actor_in_same_phase(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()

    await repo.create(
        case_id=case.id,
        phase_id=phase.id,
        actor_player_id=players[0].id,
        action_type=ActionType.NIGHT_ACTION_RED_VOTE,
        night_target_seat_no=players[1].seat_no,
    )
    await db_session.commit()

    # when / then
    with pytest.raises(IntegrityError):
        await repo.create(
            case_id=case.id,
            phase_id=phase.id,
            actor_player_id=players[0].id,
            action_type=ActionType.NIGHT_ACTION_SKIP,
            night_target_seat_no=None,
        )
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.anyio
async def test_create_raises_integrity_error_when_red_vote_has_null_target(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()

    # when / then
    with pytest.raises(IntegrityError):
        await repo.create(
            case_id=case.id,
            phase_id=phase.id,
            actor_player_id=players[0].id,
            action_type=ActionType.NIGHT_ACTION_RED_VOTE,
            night_target_seat_no=None,
        )
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.anyio
async def test_create_raises_integrity_error_when_skip_has_target(
    db_session: AsyncSession,
    case_action_repo: CaseActionRepo,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    repo = case_action_repo

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()

    # when / then
    with pytest.raises(IntegrityError):
        await repo.create(
            case_id=case.id,
            phase_id=phase.id,
            actor_player_id=players[0].id,
            action_type=ActionType.NIGHT_ACTION_SKIP,
            night_target_seat_no=players[1].seat_no,
        )
        await db_session.commit()

    await db_session.rollback()
