from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.constants.case import SEAT_NO_MAX_EXCLUSIVE
from app.domain.enum import ActionType, CaseStatus, PhaseType
from app.models.base import Base


class Case(Base):
    """
    Case OR 모델
    """

    __tablename__ = "cases"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )

    host_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_"), default=CaseStatus.RUNNING, nullable=False
    )

    current_round_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_cases_room_id_status", "room_id", "status"),
        Index(
            "uq_cases_room_running",
            "room_id",
            unique=True,
            postgresql_where=(status == CaseStatus.RUNNING),
        ),
        CheckConstraint("current_round_no >= 1", name="ck_cases_round_no_positive"),
        CheckConstraint(
            "(status = 'RUNNING' AND ended_at IS NULL) "
            "OR "
            "(status = 'ENDED' AND ended_at IS NOT NULL)",
            name="ck_cases_status_ended_at_consistency",
        ),
    )


class CasePlayer(Base):
    __tablename__ = "case_players"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seat_no: Mapped[int] = mapped_column(nullable=False)
    life_left: Mapped[int] = mapped_column(nullable=False, default=2)
    vote_tokens: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("case_id", "user_id", name="uq_case_players_case_user"),
        UniqueConstraint("case_id", "seat_no", name="uq_case_players_case_seat"),
        CheckConstraint(
            f"seat_no >= 0 AND seat_no < {SEAT_NO_MAX_EXCLUSIVE}",
            name="ck_case_players_seat_no_range",
        ),
        CheckConstraint(
            "life_left >= 0 AND life_left <= 2", name="ck_case_players_life_left_range"
        ),
        CheckConstraint(
            "vote_tokens >= 0 AND vote_tokens <= 4", name="ck_case_players_vote_tokens_range"
        ),
    )


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_no: Mapped[int] = mapped_column(nullable=False)
    seq_in_round: Mapped[int] = mapped_column(nullable=False)
    phase_type: Mapped[PhaseType] = mapped_column(
        Enum(PhaseType, name="phase_type"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("case_id", "round_no", "seq_in_round", name="uq_case_round_seq"),
        CheckConstraint("round_no >= 1", name="ck_round_no_positive"),
        CheckConstraint("seq_in_round >= 1", name="ck_seq_in_round_positive"),
    )


class VotePhaseState(Base):
    __tablename__ = "vote_phase_states"

    phase_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("phases.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    target_seat_no: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            f"target_seat_no >= 0 AND target_seat_no < {SEAT_NO_MAX_EXCLUSIVE}",
            name="ck_vote_phase_states_target_seat_no_range",
        ),
    )


class CaseAction(Base):
    __tablename__ = "case_actions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor_player_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("case_players.id", ondelete="RESTRICT"),
        nullable=False,
    )

    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType, name="action_type_"), nullable=False
    )  # RED_VOTE, SKIP 등

    night_target_seat_no: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_timeout_auto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_case_actions_case_phase", "case_id", "phase_id"),
        CheckConstraint(
            f"night_target_seat_no >= 0 AND night_target_seat_no < {SEAT_NO_MAX_EXCLUSIVE}",
            name="ck_case_actions_night_target_seat_no_range",
        ),
        CheckConstraint(
            "(action_type = 'NIGHT_ACTION_RED_VOTE' AND night_target_seat_no IS NOT NULL) "
            "OR "
            "(action_type = 'NIGHT_ACTION_SKIP' AND night_target_seat_no IS NULL) "
            "OR "
            "(action_type NOT IN ('NIGHT_ACTION_RED_VOTE', 'NIGHT_ACTION_SKIP'))",
            name="ck_case_actions_action_type_target_consistency",
        ),
        UniqueConstraint("phase_id", "actor_player_id", name="uq_case_actions_phase_actor"),
    )
