from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enum import CaseStatus
from app.models.case import Case
from app.schemas.common.ids import CaseId, RoomId, UserId


class CaseRepo:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        room_id: RoomId,
        host_user_id: UserId,
        status: CaseStatus = CaseStatus.RUNNING,
        current_round_no: int = 1,
    ) -> Case:
        row = Case(
            room_id=room_id,
            host_user_id=host_user_id,
            status=status,
            current_round_no=current_round_no,
        )
        self._db.add(row)
        return row

    async def get_by_id(self, *, case_id: CaseId) -> Case | None:
        q = select(Case).where(Case.id == case_id)
        return (await self._db.execute(q)).scalar_one_or_none()

    async def get_running_by_room_id(self, *, room_id: RoomId) -> Case | None:
        q = select(Case).where(
            Case.room_id == room_id,
            Case.status == CaseStatus.RUNNING,
        )
        return (await self._db.execute(q)).scalar_one_or_none()
