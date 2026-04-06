from uuid import uuid4

import pytest

from app.domain.case_logic.night import (
    NightRuleViolationError,
    should_end_night,
    validate_red_vote,
)

# -----------------------------
# validate_red_vote
# -----------------------------


def test_validate_red_vote_success():
    actor_id = uuid4()
    alive_ids = {actor_id, uuid4()}

    # should not raise
    validate_red_vote(
        is_night_phase=True,
        actor_player_id=actor_id,
        alive_player_ids=alive_ids,
        target_seat_no=1,
        actor_seat_no=0,
        max_seat_no=4,
        alive_seat_nos={0, 1},
        already_acted=False,
    )


def test_validate_red_vote_skip_success():
    actor_id = uuid4()
    alive_ids = {actor_id}

    validate_red_vote(
        is_night_phase=True,
        actor_player_id=actor_id,
        alive_player_ids=alive_ids,
        target_seat_no=None,  # skip
        actor_seat_no=0,
        max_seat_no=4,
        alive_seat_nos={0},
        already_acted=False,
    )


def test_validate_red_vote_not_night():
    with pytest.raises(NightRuleViolationError):
        validate_red_vote(
            is_night_phase=False,
            actor_player_id=uuid4(),
            alive_player_ids=set(),
            target_seat_no=1,
            actor_seat_no=0,
            max_seat_no=4,
            alive_seat_nos=set(),
            already_acted=False,
        )


def test_validate_red_vote_not_alive():
    actor_id = uuid4()

    with pytest.raises(NightRuleViolationError):
        validate_red_vote(
            is_night_phase=True,
            actor_player_id=actor_id,
            alive_player_ids=set(),
            target_seat_no=1,
            actor_seat_no=0,
            max_seat_no=4,
            alive_seat_nos=set(),
            already_acted=False,
        )


def test_validate_red_vote_already_acted():
    actor_id = uuid4()

    with pytest.raises(NightRuleViolationError):
        validate_red_vote(
            is_night_phase=True,
            actor_player_id=actor_id,
            alive_player_ids={actor_id},
            target_seat_no=1,
            actor_seat_no=0,
            max_seat_no=4,
            alive_seat_nos={0, 1},
            already_acted=True,
        )


def test_validate_red_vote_invalid_seat():
    actor_id = uuid4()

    with pytest.raises(NightRuleViolationError):
        validate_red_vote(
            is_night_phase=True,
            actor_player_id=actor_id,
            alive_player_ids={actor_id},
            target_seat_no=5,  # out of range
            actor_seat_no=0,
            max_seat_no=4,
            alive_seat_nos={0, 1, 2, 3},
            already_acted=False,
        )


def test_validate_red_vote_self_vote():
    actor_id = uuid4()

    with pytest.raises(NightRuleViolationError):
        validate_red_vote(
            is_night_phase=True,
            actor_player_id=actor_id,
            alive_player_ids={actor_id},
            target_seat_no=1,
            actor_seat_no=1,
            max_seat_no=4,
            alive_seat_nos={0, 1},
            already_acted=False,
        )


def test_validate_red_vote_dead_target():
    actor_id = uuid4()

    with pytest.raises(NightRuleViolationError):
        validate_red_vote(
            is_night_phase=True,
            actor_player_id=actor_id,
            alive_player_ids={actor_id},
            target_seat_no=1,
            actor_seat_no=0,
            max_seat_no=4,
            alive_seat_nos={0, 2, 3},
            already_acted=False,
        )


# -----------------------------
# should_end_night
# -----------------------------


def test_should_end_night_true():
    assert should_end_night(alive_player_count=4, action_count=4) is True


def test_should_end_night_false():
    assert should_end_night(alive_player_count=4, action_count=3) is False
