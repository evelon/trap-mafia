from __future__ import annotations

import asyncio
import uuid
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.auth import User
from app.models.room import Room, RoomMember
from app.mvp import MVP_ROOM_ID
from app.schemas.common.ids import RoomId, UserId


async def create_user(db, *, username: str) -> uuid.UUID:
    user = User(id=uuid4(), username=username)
    db.add(user)
    await db.commit()
    return user.id


async def create_room(db: AsyncSession, *, host_id: UUID) -> UUID:
    # MVP: Only one room exists
    room = await db.get(Room, MVP_ROOM_ID)
    assert room is not None
    room.host_id = host_id
    await db.commit()
    return MVP_ROOM_ID

    room_id = uuid4()
    db.add(Room(id=room_id, host_id=host_id))
    await db.commit()
    return room_id


async def _create_room_with_members(db: AsyncSession, user_ids: list[UserId]) -> RoomId:

    # room = Room(name="test_room", host_id=user_ids[0]) # when not MVP
    q = select(User).where(User.id.in_(user_ids))
    result = await db.execute(q)
    users = result.scalars().all()
    # db.add(room)
    await db.commit()
    # await db.refresh(room)
    room_id = await create_room(db, host_id=user_ids[0])
    members = [RoomMember(user_id=user.id, room_id=room_id) for user in users]
    db.add_all(members)
    await db.commit()

    return room_id


async def _create_user(db: AsyncSession, username: str) -> User:
    user = User(username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def room_with_members(
    db: AsyncSession,
    usernames: list[str] | None = None,
) -> tuple[RoomId, list[UserId]]:
    if usernames is None:
        usernames = ["username1", "username2", "username3", "username4"]
    user_ids: list[UserId] = []
    for username in usernames:
        try:
            user = await _create_user(db, username)
            await asyncio.sleep(0.5)
            user_ids.append(user.id)
        except IntegrityError:
            await db.rollback()
            q = select(User).where(User.username == username)
            user = (await db.execute(q)).scalar_one()
            user_ids.append(user.id)
            continue
    room_id = await _create_room_with_members(db, user_ids)
    return room_id, user_ids
