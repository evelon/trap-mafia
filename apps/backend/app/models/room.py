from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.auth import User
from app.models.base import Base


class Room(Base):
    """
    Room ORM 모델

    - users.host_id -> users.id
    - room_members와 1:N 관계
    """

    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # MVP: To be false
    )

    host: Mapped["User"] = relationship(
        "User",
        back_populates="hosted_rooms",
        foreign_keys=[host_id],
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    members: Mapped[list["RoomMember"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )


class RoomMember(Base):
    """
    RoomMember ORM 모델

    - composite primary key: (room_id, user_id)
    - active membership 정의: left_at IS NULL
    """

    __tablename__ = "room_members"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="room_memberships",
        foreign_keys=[user_id],
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    room: Mapped["Room"] = relationship(
        back_populates="members",
    )
