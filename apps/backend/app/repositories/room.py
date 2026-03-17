from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.mvp import MVP_ROOM_ID
from app.schemas.common.ids import RoomId, UserId


class RoomRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, *, host_id: UserId, room_name: str) -> Room:
        query = select(Room).where(Room.id == MVP_ROOM_ID)
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()

        if room is None:
            room = Room(
                id=MVP_ROOM_ID,
                host_id=host_id,
                name=room_name,
            )
            self.db.add(room)
            await self.db.flush()
            return room

        room.host_id = host_id
        room.name = room_name
        await self.db.flush()
        return room

    async def get_by_id(self, *, room_id: RoomId) -> Room | None:
        query = select(Room).where(Room.id == room_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
