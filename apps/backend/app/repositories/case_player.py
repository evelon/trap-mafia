from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseTeam
from app.models.case import CasePlayer
from app.schemas.common.ids import CaseId, UserId


class CasePlayerRepo:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_many(
        self,
        *,
        case_id: CaseId,
        user_ids: list[UserId],
    ) -> list[CasePlayer]:
        rows = [
            CasePlayer(
                case_id=case_id,
                user_id=user_id,
                team=CaseTeam.BLUE if seat_no % 2 == 0 else CaseTeam.RED,
                seat_no=seat_no,
                vote_tokens=1,
            )
            for seat_no, user_id in enumerate(user_ids)
        ]
        self._db.add_all(rows)
        return rows

    async def list_by_case_id(self, *, case_id: CaseId) -> list[CasePlayer]:
        q = select(CasePlayer).where(CasePlayer.case_id == case_id).order_by(CasePlayer.seat_no)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_by_case_id_and_user_id(
        self, *, case_id: CaseId, user_id: UserId
    ) -> CasePlayer | None:
        q = select(CasePlayer).where(CasePlayer.case_id == case_id, CasePlayer.user_id == user_id)
        result = await self._db.execute(q)
        return result.scalar_one_or_none()
