from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_snapshot import CaseSnapshotHistory
from app.schemas.common.ids import CaseId


class CaseSnapshotHistoryRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_latest_by_case_id(self, *, case_id: CaseId) -> CaseSnapshotHistory | None:
        q = (
            select(CaseSnapshotHistory)
            .where(CaseSnapshotHistory.case_id == case_id)
            .order_by(CaseSnapshotHistory.snapshot_no.desc())
            .limit(1)
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def get_by_snapshot_no(
        self, *, case_id: CaseId, snapshot_no: int
    ) -> CaseSnapshotHistory | None:
        q = select(CaseSnapshotHistory).where(
            CaseSnapshotHistory.case_id == case_id, CaseSnapshotHistory.snapshot_no == snapshot_no
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def get_after_snapshot_no(
        self, *, case_id: CaseId, last_seen_no: int
    ) -> list[CaseSnapshotHistory]:
        q = (
            select(CaseSnapshotHistory)
            .where(
                CaseSnapshotHistory.case_id == case_id,
                CaseSnapshotHistory.snapshot_no > last_seen_no,
            )
            .order_by(CaseSnapshotHistory.snapshot_no)
        )
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        case_id,
        snapshot_no: int,
        schema_version: int,
        snapshot_json: dict,
    ) -> CaseSnapshotHistory:
        row = CaseSnapshotHistory(
            case_id=case_id,
            snapshot_no=snapshot_no,
            schema_version=schema_version,
            snapshot_json=snapshot_json,
        )
        self.db.add(row)
        return row
