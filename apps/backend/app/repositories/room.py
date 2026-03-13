from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room


class RoomRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, *, room_id: UUID) -> Room | None:
        return (await self.db.execute(select(Room).where(Room.id == room_id))).scalar_one_or_none()
