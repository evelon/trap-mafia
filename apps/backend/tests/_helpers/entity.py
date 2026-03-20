from __future__ import annotations

import uuid
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.auth import User
from app.models.room import Room
from app.mvp import MVP_ROOM_ID
from tests.integration.services.test_case_service import _create_room_with_members, _create_user


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


async def room_with_members(
    db: AsyncSession, usernames: list[str] | None = None
) -> tuple[Room, list[User]]:
    if usernames is None:
        usernames = ["username1", "username2", "username3", "username4"]
    users = [await _create_user(db, username) for username in usernames]
    room = await _create_room_with_members(db, users)
    return room, users
