from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.constants import SEAT_NO_MAX_EXCLUSIVE
from app.domain.enum import CaseStatus, PhaseType, VoteFailReason, VoteType
from app.domain.types import SeatNo
from app.schemas.common.datetime import UtcDateTime


class CaseState(BaseModel):
    case_id: UUID = UUID("00000000-0000-0000-0000-000000000000")
    status: CaseStatus = CaseStatus.RUNNING
    round_no: Annotated[int, Field(ge=0)]


class PhaseState(BaseModel):
    phase_id: UUID
    history_id: Annotated[int, Field(ge=0)] = 0
    phase_type: PhaseType
    seq_in_round: Annotated[int, Field(ge=0)]
    phase_no_in_round: Annotated[int, Field(ge=0)]
    opened_at: UtcDateTime = "1970-01-01T00:00:00.000Z"


class Player(BaseModel):
    username: str  # only in MVP
    seat_no: SeatNo
    life_lost: Annotated[int, Field(ge=0)]
    vote_tokens: Annotated[int, Field(ge=0, le=4)]
    eliminated: bool


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
    schema_version: Annotated[int, Field(ge=1)]
    case_state: CaseState
    phase_state: PhaseState
    players: Annotated[list[Player], Field(max_length=SEAT_NO_MAX_EXCLUSIVE)]
    night_phase_info: NightPhaseInfo
    vote_phase_info: VotePhaseInfo
    discuss_phase_info: DiscussPhaseInfo
    logs: list[str]
