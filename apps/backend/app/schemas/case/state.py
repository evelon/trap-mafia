from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.domain.constants.case import (
    BLUE_VOTE_MAX_EXCLUSIVE,
    SEAT_MAX_EXCLUSIVE,
    SEAT_MIN,
    SEAT_NO_MAX_EXCLUSIVE,
    SEAT_NO_MIN,
)
from app.domain.enum import CaseStatus, PhaseType, VoteFailReason
from app.domain.types import SeatNo
from app.schemas.base import RequiredFieldsModel
from app.schemas.common.datetime import UtcDatetime
from app.schemas.common.ids import CaseId, PhaseId


class CaseState(RequiredFieldsModel):
    case_id: CaseId
    status: CaseStatus = CaseStatus.RUNNING
    round_no: Annotated[int, Field(ge=1)]


class PhaseState(RequiredFieldsModel):
    phase_id: PhaseId
    phase_type: PhaseType
    seq_in_round: Annotated[int, Field(ge=1)]
    phase_no_in_round: Annotated[int, Field(ge=1)]
    created_at: UtcDatetime


class Player(RequiredFieldsModel):
    user_id: UUID
    username: str  # only in MVP
    seat_no: SeatNo
    life_left: Annotated[int, Field(ge=0)]
    vote_tokens: Annotated[int, Field(ge=0, le=4)]


class NightPhaseResult(RequiredFieldsModel):
    player_damaged: Annotated[int | None, Field(ge=SEAT_NO_MIN, lt=SEAT_NO_MAX_EXCLUSIVE)]
    fail_reason: None | VoteFailReason


class BlueVoteInitResult(RequiredFieldsModel):
    targeter_seat_no: SeatNo
    targeted_seat_no: SeatNo


class VotePhaseResult(RequiredFieldsModel):
    player_damaged: Annotated[int, Field(ge=SEAT_NO_MIN, lt=SEAT_NO_MAX_EXCLUSIVE)]
    fail_reason: None | VoteFailReason
    blue_vote_left: Annotated[int, Field(ge=0, lt=BLUE_VOTE_MAX_EXCLUSIVE)]


class RoundEndResult(RequiredFieldsModel):
    pass


class CaseSnapshot(RequiredFieldsModel):
    schema_version: Annotated[int, Field(ge=1, default=1)]
    snapshot_no: Annotated[int, Field(ge=1)] = 1
    case_state: CaseState
    phase_state: PhaseState
    players: Annotated[list[Player], Field(min_length=SEAT_MIN, max_length=SEAT_MAX_EXCLUSIVE)]
    night_phase_result: NightPhaseResult | None
    blue_vote_init_result: BlueVoteInitResult | None
    vote_phase_result: VotePhaseResult | None
    round_end_result: RoundEndResult | None
    logs: list[str]
