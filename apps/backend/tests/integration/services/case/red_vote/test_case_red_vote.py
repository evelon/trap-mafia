from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.case_logic.night import NightRuleViolationError
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

    assert len(fake_pubsub.published) == 0


@pytest.mark.anyio
async def test_red_vote_rejects_duplicate_action_in_same_night(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    # given
    case, players = started_case_with_players

    actor = players[0]
    target = players[1]

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
    result = await db_session.execute(select(CaseSnapshotHistory))
    histories = result.scalars().all()
    assert len(histories) == before_count + 1

    result = await db_session.execute(select(Phase))
    phases = result.scalars().all()
    assert len(phases) >= 2

    assert len(fake_pubsub.published) == 1
