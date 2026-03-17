from datetime import datetime, timezone
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class RoomSnapshotType(str, Enum):
    ON_CONNECT = "room.connected"
    MEMBER_JOINED = "room.member.joined"
    MEMBER_LEFT = "room.member.left"
    MEMBER_KICKED = "room.member.kicked"
    MEMBER_READY = "room.member.readied"
    MEMBER_UNREADY = "room.member.unreadied"
    CASE_STARTED = "room.case.started"
    CASE_ENDED = "room.case.ended"
    STREAM_CLOSE = "room.stream_close"


class RoomEventDelta(BaseModel):
    type: RoomSnapshotType
    user_id: UUID | None = None
    ts: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone.utc))]
    version: int | None = None
