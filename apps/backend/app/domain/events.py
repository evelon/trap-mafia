from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RoomEventType(str, Enum):
    ROOM_SNAPSHOT = "room.snapshot"
    MEMBER_JOINED = "room.member.joined"
    MEMBER_LEFT = "room.member.left"
    MEMBER_KICKED = "room.member.kicked"


class RoomEvent(BaseModel):
    id: str  # ULID 추천, 없으면 uuid4
    type: RoomEventType
    room_id: str
    ts: datetime = Field(default_factory=lambda: datetime.utcnow())
    data: Any | None = None
