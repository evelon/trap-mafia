from datetime import datetime
from typing import NamedTuple
from uuid import UUID


class SnapshotRoomMember(NamedTuple):
    user_id: UUID
    username: str
    joined_at: datetime
