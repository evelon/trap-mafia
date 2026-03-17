from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case


class CaseRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_running_by_room_id(self, *, room_id: UUID) -> Case | None:
        q = select(Case).where(Case.room_id == room_id, Case.status == "RUNNING").limit(1)
        return (await self.db.execute(q)).scalar_one_or_none()
