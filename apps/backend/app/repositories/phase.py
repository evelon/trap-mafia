from sqlalchemy import func, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.exceptions import raise_conflict
from app.domain.enum import PhaseType
from app.models.case import Phase
from app.schemas.common.ids import CaseId, PhaseId
from app.schemas.room.response import CaseStartConflictCode

INITIAL_ROUND_NO = 1
INITIAL_SEQ_IN_ROUND = 1


class PhaseRepo:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, case_id: CaseId) -> Phase:
        phase = Phase(
            case_id=case_id,
            round_no=INITIAL_ROUND_NO,
            seq_in_round=INITIAL_SEQ_IN_ROUND,
            phase_type=PhaseType.NIGHT,
        )
        self._db.add(phase)
        await self._db.commit()
        await self._db.refresh(phase)
        return phase

    async def _close(self, where_clause) -> Phase:
        q = update(Phase).where(where_clause).values(closed_at=func.now())
        result = await self._db.execute(q)
        if result.row_count != 1:  # type: ignore[attr-defined]
            raise_conflict(code=CaseStartConflictCode.ROOM_CASE_RUNNING)
        return result.scalar_one()

    async def close_by_phase_id(self, phase_id: PhaseId) -> Phase:
        return await self._close(Phase.id == phase_id)

    async def close_by_case_id(self, case_id: CaseId) -> Phase:
        return await self._close(Phase.case_id == case_id)
