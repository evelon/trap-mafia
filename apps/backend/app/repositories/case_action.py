from __future__ import annotations

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enum import ActionType
from app.models.case import CaseAction
from app.schemas.common.ids import CaseId, PhaseId, PlayerId


class CaseActionRepo:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        case_id: CaseId,
        phase_id: PhaseId,
        actor_player_id: PlayerId,
        action_type: ActionType,
        night_target_seat_no: int | None = None,
        is_timeout_auto: bool = False,
    ) -> CaseAction:
        case_action = CaseAction(
            case_id=case_id,
            phase_id=phase_id,
            actor_player_id=actor_player_id,
            action_type=action_type,
            night_target_seat_no=night_target_seat_no,
            is_timeout_auto=is_timeout_auto,
        )
        self._db.add(case_action)
        await self._db.flush()
        return case_action

    async def exists_by_phase_and_actor(
        self,
        *,
        phase_id: PhaseId,
        actor_player_id: PlayerId,
    ) -> bool:
        q = select(
            exists().where(
                CaseAction.phase_id == phase_id, CaseAction.actor_player_id == actor_player_id
            )
        )
        result = await self._db.execute(q)
        return bool(result.scalar_one())

    async def count_by_phase_id(
        self,
        *,
        phase_id: PhaseId,
    ) -> int:
        q = select(func.count()).select_from(CaseAction).where(CaseAction.phase_id == phase_id)
        result = await self._db.execute(q)
        return int(result.scalar_one())

    async def list_by_phase_id(
        self,
        *,
        phase_id: PhaseId,
    ) -> list[CaseAction]:
        q = (
            select(CaseAction)
            .where(CaseAction.phase_id == phase_id)
            .order_by(CaseAction.created_at.asc())
        )
        result = await self._db.execute(q)
        return list(result.scalars().all())
