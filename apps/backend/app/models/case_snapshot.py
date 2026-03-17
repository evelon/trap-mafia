from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CaseSnapshotHistory(Base):
    """
    Case snapshot history OR 모델

    - case의 시점별 snapshot을 저장한다.
    - snapshot_no는 case 단위 증가값이다.
    - snapshot_json이 authoritative snapshot payload다.
    """

    __tablename__ = "case_snapshot_history"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    case_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    snapshot_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    snapshot_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "case_id",
            "snapshot_no",
            name="uq_case_snapshot_history_case_snapshot_no",
        ),
        CheckConstraint("snapshot_no >= 1", name="ck_case_snapshot_history_snapshot_no_positive"),
        CheckConstraint(
            "schema_version >= 1", name="ck_case_snapshot_history_schema_version_positive"
        ),
        Index(
            "ix_case_snapshot_history_case_id_snapshot_no_desc",
            "case_id",
            "snapshot_no",
        ),
    )
