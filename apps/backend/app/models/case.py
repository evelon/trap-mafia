from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enum import CaseStatus
from app.models.base import Base


class Case(Base):
    """
    Case OR 모델
    """

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )

    host_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status"), default=CaseStatus.RUNNING, nullable=False
    )

    current_round_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
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
