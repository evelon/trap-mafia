from __future__ import annotations

import uuid
from uuid import UUID, uuid4

from app.models.auth import User
from app.models.room import Room
from app.mvp import MVP_ROOM_ID


async def create_user(db, *, username: str) -> uuid.UUID:
    user = User(id=uuid4(), username=username)
    db.add(user)
    await db.commit()
    return user.id


async def create_room(db, *, host_id: UUID) -> UUID:
    # MVP: Only one room exists
    return MVP_ROOM_ID
    room_id = uuid4()
    db.add(Room(id=room_id, host_id=host_id))
    await db.commit()
    return room_id
