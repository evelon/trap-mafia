from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.case_logic.night import NightRuleViolationError
from app.domain.enum import PhaseType
from app.models.case import Case, CaseAction, CasePlayer, Phase
from app.models.case_snapshot import CaseSnapshotHistory
from app.services.case import CaseService
from tests.conftest import FakePubSub


@pytest.mark.anyio
async def test_red_vote_creates_case_action(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players

    actor = players[0]
    target = players[1]

    # when

    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=actor.id,
        target_seat_no=target.seat_no,
    )
    # then
    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()

    assert len(actions) == 1
    assert actions[0].case_id == case.id
    assert actions[0].night_target_seat_no == target.seat_no


@pytest.mark.anyio
async def test_red_vote_skip_creates_case_action_with_null_target(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):

    # given
    case, players = started_case_with_players

    actor = players[0]

    # when
    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=actor.id,
        target_seat_no=None,
    )

    # then
    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()

    assert len(actions) == 1
    assert actions[0].case_id == case.id
    assert actions[0].night_target_seat_no is None


@pytest.mark.anyio
async def test_red_vote_service_does_not_end_night_on_partial_votes(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
    fake_pubsub: FakePubSub,
):

    before_publish_count = len(fake_pubsub.published)

    # given
    case, players = started_case_with_players

    actor = players[0]
    target = players[1]

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1

    actor = players[0]
    target = players[1]

    # when
    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=actor.id,
        target_seat_no=target.seat_no,
    )

    # then
    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    result = await db_session.execute(select(Phase))
    phases = result.scalars().all()
    assert len(phases) == 1
    assert len(fake_pubsub.published) == before_publish_count


@pytest.mark.anyio
async def test_red_vote_rejects_duplicate_action_in_same_night(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players

    # (removed duplicate actor/target assignment)

    actor = players[0]
    target = players[1]

    # when
    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=actor.id,
        target_seat_no=target.seat_no,
    )

    # then
    with pytest.raises(NightRuleViolationError):
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=players[2].seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()
    assert len(actions) == 1


@pytest.mark.anyio
async def test_red_vote_service_last_vote_ends_night(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
    fake_pubsub: FakePubSub,
):
    before_publish_count = len(fake_pubsub.published)
    # given
    case, players = started_case_with_players

    actor = players[0]
    target = players[1]

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1

    # when
    for i, actor in enumerate(players):
        target = players[(i + 1) % len(players)]
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=target.seat_no,
        )

    # then
    result1 = await db_session.execute(select(CaseSnapshotHistory))
    histories = result1.scalars().all()
    assert len(histories) == before_count + 1

    result2 = await db_session.execute(select(Phase))
    phases = result2.scalars().all()
    assert len(phases) >= 2

    active_phases = [phase for phase in phases if phase.closed_at is None]
    assert len(active_phases) == 1
    assert active_phases[0].phase_type == PhaseType.DISCUSS

    closed_night_phases = [
        phase
        for phase in phases
        if phase.phase_type == PhaseType.NIGHT and phase.closed_at is not None
    ]
    assert len(closed_night_phases) == 1

    assert len(fake_pubsub.published) == before_publish_count + 1


@pytest.mark.anyio
async def test_red_vote_rejects_self_vote(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    actor = players[0]

    # when / then
    with pytest.raises(NightRuleViolationError):
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=actor.seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()
    assert len(actions) == 0


@pytest.mark.anyio
async def test_red_vote_rejects_invalid_target_seat(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    actor = players[0]
    invalid_seat_no = len(players)

    # when / then
    with pytest.raises(NightRuleViolationError):
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=invalid_seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()
    assert len(actions) == 0


@pytest.mark.anyio
async def test_red_vote_rejects_when_actor_is_not_alive(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    actor = players[0]
    target = players[1]

    actor.life_left = 0
    await db_session.commit()

    # when / then
    with pytest.raises(NightRuleViolationError):
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=target.seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()
    assert len(actions) == 0


@pytest.mark.anyio
async def test_red_vote_rejects_when_current_phase_is_not_night(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    actor = players[0]
    target = players[1]

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case.id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()
    phase.phase_type = PhaseType.DISCUSS
    await db_session.commit()

    # when / then
    with pytest.raises(NightRuleViolationError):
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=target.seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()
    assert len(actions) == 0


@pytest.mark.anyio
async def test_red_vote_all_skips_end_night(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
    fake_pubsub: FakePubSub,
):

    before_publish_count = len(fake_pubsub.published)

    # given
    case, players = started_case_with_players

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1
    alive_players = [player for player in players if player.life_left != 0]

    # when
    for actor in alive_players:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=actor.id,
            target_seat_no=None,
        )

    # then
    result1 = await db_session.execute(select(CaseSnapshotHistory))
    histories = result1.scalars().all()
    assert len(histories) == before_count + 1

    result2 = await db_session.execute(select(Phase))
    phases = result2.scalars().all()
    assert len(phases) >= 2

    active_phases = [phase for phase in phases if phase.closed_at is None]
    assert len(active_phases) == 1
    assert active_phases[0].phase_type == PhaseType.DISCUSS

    closed_night_phases = [
        phase
        for phase in phases
        if phase.phase_type == PhaseType.NIGHT and phase.closed_at is not None
    ]
    assert len(closed_night_phases) == 1

    assert len(fake_pubsub.published) == before_publish_count + 1


# Additional tests


@pytest.mark.skip(reason="other rooms not yet exist")
@pytest.mark.anyio
async def test_red_vote_rejects_actor_player_from_another_case(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players
    target = players[1]

    other_mut = await case_service.start_case(room_id=case.room_id)
    result = await db_session.execute(
        select(CasePlayer)
        .where(CasePlayer.case_id == other_mut.subject_id)
        .order_by(CasePlayer.seat_no)
    )
    other_case_players = result.scalars().all()
    other_actor = other_case_players[0]

    # when / then
    with pytest.raises(NightRuleViolationError):
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=other_actor.id,
            target_seat_no=target.seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = [action for action in result.scalars().all() if action.case_id == case.id]
    assert len(actions) == 0


@pytest.mark.anyio
async def test_red_vote_rejects_when_case_is_not_found(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    _case, players = started_case_with_players
    actor = players[0]
    target = players[1]

    missing_case_id = _case.id.__class__("ffffffff-ffff-ffff-ffff-ffffffffffff")

    # when / then
    with pytest.raises(Exception):
        await case_service.red_vote(
            case_id=missing_case_id,
            actor_player_id=actor.id,
            target_seat_no=target.seat_no,
        )

    result = await db_session.execute(select(CaseAction))
    actions = result.scalars().all()
    assert len(actions) == 0
