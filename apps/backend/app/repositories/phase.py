from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.error_codes import ConflictErrorCode
from app.core.exceptions import raise_conflict
from app.domain.enum import PhaseTransitType, PhaseType
from app.models.case import Phase
from app.schemas.common.ids import CaseId, PhaseId

INITIAL_ROUND_NO = 1
INITIAL_SEQ_IN_ROUND = 1


class PhaseRepo:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _get_latest_phase(self, case_id):
        q = select(Phase).where(Phase.case_id == case_id).order_by(desc(Phase.created_at)).limit(1)
        res = await self._db.execute(q)
        phase = res.scalar_one_or_none()
        if phase is None:
            raise_conflict(code=ConflictErrorCode.CONFLICT_PHASE_NOT_FOUND)
        return phase

    async def _set_next_phase(self, prev_phase: Phase, transit_type: PhaseTransitType):
        ...
        return prev_phase

    async def create(
        self, *, case_id: CaseId, transit_type: PhaseTransitType | None = None
    ) -> Phase:
        if transit_type is None:
            phase = Phase(
                case_id=case_id,
                round_no=INITIAL_ROUND_NO,
                seq_in_round=INITIAL_SEQ_IN_ROUND,
                phase_type=PhaseType.NIGHT,
            )
        else:
            latest_phase = await self._get_latest_phase(case_id)
            phase = await self._set_next_phase(latest_phase, transit_type)
        self._db.add(phase)
        await self._db.commit()
        await self._db.refresh(phase)
        return phase

    async def _close(self, where_clause) -> Phase:
        q = update(Phase).where(where_clause).values(closed_at=func.now())
        result = await self._db.execute(q)
        if result.row_count != 1:  # type: ignore[attr-defined]
            raise_conflict(code=ConflictErrorCode.CONFLICT_ROOM_CASE_RUNNING)
        return result.scalar_one()

    async def close_by_phase_id(self, phase_id: PhaseId) -> Phase:
        return await self._close(Phase.id == phase_id)

    async def close_by_case_id(self, case_id: CaseId) -> Phase:
        return await self._close(Phase.case_id == case_id)
