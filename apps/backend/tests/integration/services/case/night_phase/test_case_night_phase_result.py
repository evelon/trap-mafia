from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enum import CaseTeam, VoteFailReason
from app.models.case import Case, CasePlayer
from app.models.case_snapshot import CaseSnapshotHistory
from app.schemas.case.state import CaseSnapshot
from app.services.case import CaseService


async def _get_latest_snapshot(db_session: AsyncSession, *, case_id) -> CaseSnapshot:
    result = await db_session.execute(
        select(CaseSnapshotHistory)
        .where(CaseSnapshotHistory.case_id == case_id)
        .order_by(CaseSnapshotHistory.snapshot_no.desc())
    )
    latest = result.scalars().first()
    assert latest is not None
    return CaseSnapshot.model_validate(latest.snapshot_json)


def _assert_only_night_result_is_set(snapshot: CaseSnapshot) -> None:
    assert snapshot.night_phase_result is not None
    assert snapshot.blue_vote_init_result is None
    assert snapshot.vote_phase_result is None
    assert snapshot.round_end_result is None


@pytest.mark.anyio
async def test_night_phase_result_sets_damaged_player_on_valid_red_vote(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    case, players = started_case_with_players

    red_players = [player for player in players if player.team == CaseTeam.RED]
    blue_players = [player for player in players if player.team == CaseTeam.BLUE]
    target = blue_players[0]

    for red_player in red_players:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=red_player.id,
            target_seat_no=target.seat_no,
        )
    for blue_player in blue_players:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=blue_player.id,
            target_seat_no=None,
        )

    await db_session.refresh(target)
    assert target.life_left == 1

    snapshot = await _get_latest_snapshot(db_session, case_id=case.id)
    _assert_only_night_result_is_set(snapshot)

    assert snapshot.night_phase_result
    assert snapshot.night_phase_result.player_damaged == target.seat_no
    assert snapshot.night_phase_result.fail_reason is None


@pytest.mark.anyio
async def test_night_phase_result_sets_tie_fail_reason_on_tied_red_vote(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    case, players = started_case_with_players

    red_players = [player for player in players if player.team == CaseTeam.RED]
    blue_players = [player for player in players if player.team == CaseTeam.BLUE]

    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=red_players[0].id,
        target_seat_no=blue_players[0].seat_no,
    )
    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=red_players[1].id,
        target_seat_no=blue_players[1].seat_no,
    )
    for blue_player in blue_players:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=blue_player.id,
            target_seat_no=None,
        )

    await db_session.refresh(blue_players[0])
    await db_session.refresh(blue_players[1])
    assert blue_players[0].life_left == 2
    assert blue_players[1].life_left == 2

    snapshot = await _get_latest_snapshot(db_session, case_id=case.id)
    _assert_only_night_result_is_set(snapshot)
    assert snapshot.night_phase_result
    assert snapshot.night_phase_result.player_damaged is None
    assert snapshot.night_phase_result.fail_reason == VoteFailReason.TIE


@pytest.mark.anyio
async def test_night_phase_result_sets_solo_vote_fail_reason_when_only_one_participant(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    case, players = started_case_with_players

    red_players = [player for player in players if player.team == CaseTeam.RED]
    blue_players = [player for player in players if player.team == CaseTeam.BLUE]
    solo_actor = red_players[0]
    target = blue_players[0]

    await case_service.red_vote(
        case_id=case.id,
        actor_player_id=solo_actor.id,
        target_seat_no=target.seat_no,
    )
    for player in players:
        if player.id == solo_actor.id:
            continue
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=player.id,
            target_seat_no=None,
        )

    await db_session.refresh(target)
    assert target.life_left == 2

    snapshot = await _get_latest_snapshot(db_session, case_id=case.id)
    _assert_only_night_result_is_set(snapshot)
    assert snapshot.night_phase_result
    assert snapshot.night_phase_result.player_damaged is None
    assert snapshot.night_phase_result.fail_reason == VoteFailReason.SOLO_VOTE


@pytest.mark.anyio
async def test_night_phase_result_sets_no_vote_fail_reason_when_only_blue_votes_count(
    db_session: AsyncSession,
    case_service: CaseService,
    started_case_with_players: tuple[Case, list[CasePlayer]],
):
    case, players = started_case_with_players

    red_players = [player for player in players if player.team == CaseTeam.RED]
    blue_players = [player for player in players if player.team == CaseTeam.BLUE]
    target = red_players[0]

    for blue_player in blue_players:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=blue_player.id,
            target_seat_no=target.seat_no,
        )
    for red_player in red_players:
        await case_service.red_vote(
            case_id=case.id,
            actor_player_id=red_player.id,
            target_seat_no=None,
        )

    await db_session.refresh(target)
    assert target.life_left == 2

    snapshot = await _get_latest_snapshot(db_session, case_id=case.id)
    _assert_only_night_result_is_set(snapshot)
    assert snapshot.night_phase_result
    assert snapshot.night_phase_result.player_damaged is None
    assert snapshot.night_phase_result.fail_reason == VoteFailReason.NO_VOTE
