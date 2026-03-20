from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.constants.case import SEAT_MAX_EXCLUSIVE, SEAT_MIN
from app.domain.enum import CaseStatus, PhaseType, VoteFailReason, VoteType
from app.domain.types import SeatNo
from app.schemas.common.datetime import UtcDatetime
from app.schemas.common.ids import CaseId


class CaseState(BaseModel):
    case_id: CaseId
    status: CaseStatus = CaseStatus.RUNNING
    round_no: Annotated[int, Field(ge=1)]


class PhaseState(BaseModel):
    phase_id: UUID
    history_id: Annotated[int, Field(ge=1)] = 1
    phase_type: PhaseType
    seq_in_round: Annotated[int, Field(ge=1)]
    phase_no_in_round: Annotated[int, Field(ge=1)]
    opened_at: UtcDatetime


class Player(BaseModel):
    username: str  # only in MVP
    seat_no: SeatNo
    life_left: Annotated[int, Field(ge=0)]
    vote_tokens: Annotated[int, Field(ge=0, le=4)]


class NightPhaseInfo(BaseModel):
    pass


class VotePhaseInfo(BaseModel):
    targeter_seat_no: SeatNo
    targeted_seat_no: SeatNo


class DiscussPhaseInfo(BaseModel):
    player_damaged: SeatNo | None
    blue_vote_left: Annotated[int, Field(ge=0, le=2)]
    last_vote_type: VoteType
    fail_reason: VoteFailReason


class CaseSnapshot(BaseModel):
    schema_version: Annotated[int, Field(ge=1, default=1)]
    case_state: CaseState
    phase_state: PhaseState
    players: Annotated[list[Player], Field(min_length=SEAT_MIN, max_length=SEAT_MAX_EXCLUSIVE)]
    night_phase_info: NightPhaseInfo | None
    vote_phase_info: VotePhaseInfo | None
    discuss_phase_info: DiscussPhaseInfo | None
    logs: list[str]
