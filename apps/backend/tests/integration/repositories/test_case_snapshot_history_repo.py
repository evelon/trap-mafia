import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.case import Case
from app.models.case_snapshot import CaseSnapshotHistory
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.schemas.common.ids import CaseId


async def _create_snapshot(
    db_session: AsyncSession,
    *,
    case_id: CaseId,
    snapshot_no: int,
    schema_version: int = 1,
    snapshot_json: dict | None = None,
) -> CaseSnapshotHistory:
    row = CaseSnapshotHistory(
        case_id=case_id,
        snapshot_no=snapshot_no,
        schema_version=schema_version,
        snapshot_json=snapshot_json or {"schema_version": 1},
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


@pytest.mark.anyio
async def test_create_adds_snapshot_history_row_without_commit(
    db_session: AsyncSession, user_case: Case
):
    repo = CaseSnapshotHistoryRepo(db_session)
    case_id = user_case.id

    row = await repo.create(
        case_id=case_id,
        snapshot_no=1,
        schema_version=1,
        snapshot_json={"schema_version": 1},
    )

    assert row.case_id == case_id
    assert row.snapshot_no == 1
    assert row.schema_version == 1

    # 여기서는 같은 session이라 identity map 때문에 보일 수 있음
    # 진짜 DB 반영 여부를 보려면 commit 후 다시 조회
    await db_session.commit()

    fetched = await repo.get_by_snapshot_no(case_id=case_id, snapshot_no=1)
    assert fetched is not None


@pytest.mark.anyio
async def test_get_by_snapshot_no_returns_row_when_exists(
    db_session: AsyncSession, user_case: Case
):
    repo = CaseSnapshotHistoryRepo(db_session)
    case_id = user_case.id

    expected = await _create_snapshot(
        db_session,
        case_id=case_id,
        snapshot_no=3,
        snapshot_json={"k": "v"},
    )

    found = await repo.get_by_snapshot_no(case_id=case_id, snapshot_no=3)

    assert found is not None
    assert found.id == expected.id
    assert found.snapshot_no == 3
    assert found.snapshot_json == {"k": "v"}


@pytest.mark.anyio
async def test_get_by_snapshot_no_returns_none_when_missing(
    db_session: AsyncSession, user_case: Case
):
    repo = CaseSnapshotHistoryRepo(db_session)
    case_id = user_case.id

    found = await repo.get_by_snapshot_no(case_id=case_id, snapshot_no=999)

    assert found is None


@pytest.mark.anyio
async def test_get_latest_by_case_id_returns_highest_snapshot_no(
    db_session: AsyncSession, user_case: Case
):
    repo = CaseSnapshotHistoryRepo(db_session)
    case_id = user_case.id

    await _create_snapshot(db_session, case_id=case_id, snapshot_no=1)
    await _create_snapshot(db_session, case_id=case_id, snapshot_no=2)
    latest = await _create_snapshot(db_session, case_id=case_id, snapshot_no=5)

    found = await repo.get_latest_by_case_id(case_id=case_id)

    assert found is not None
    assert found.id == latest.id
    assert found.snapshot_no == 5


@pytest.mark.anyio
async def test_get_latest_by_case_id_returns_none_when_no_snapshot(
    db_session: AsyncSession, user_case: Case
):
    repo = CaseSnapshotHistoryRepo(db_session)
    case_id = user_case.id

    found = await repo.get_latest_by_case_id(case_id=case_id)
    assert found is None


# Not in MVP
# @pytest.mark.anyio
# async def test_get_after_snapshot_no_returns_rows_strictly_after_and_in_order(
#     db_session: AsyncSession, user_case: Case, user2_case: Case
# ):
#     repo = CaseSnapshotHistoryRepo(db_session)
#     case_id = user_case.id
#     other_case_id = user2_case.id

#     await _create_snapshot(db_session, case_id=case_id, snapshot_no=1)
#     await _create_snapshot(db_session, case_id=case_id, snapshot_no=2)
#     s3 = await _create_snapshot(db_session, case_id=case_id, snapshot_no=3)
#     s4 = await _create_snapshot(db_session, case_id=case_id, snapshot_no=4)

#     # 다른 case 데이터는 섞이면 안 됨
#     await _create_snapshot(db_session, case_id=other_case_id, snapshot_no=999)

#     found = await repo.get_after_snapshot_no(case_id=case_id, last_seen_no=2)

#     assert [row.snapshot_no for row in found] == [3, 4]
#     assert [row.id for row in found] == [s3.id, s4.id]


@pytest.mark.anyio
async def test_get_after_snapshot_no_returns_empty_list_when_nothing_new(
    db_session: AsyncSession, user_case: Case
):
    repo = CaseSnapshotHistoryRepo(db_session)
    case_id = user_case.id

    await _create_snapshot(db_session, case_id=case_id, snapshot_no=1)
    await _create_snapshot(db_session, case_id=case_id, snapshot_no=2)

    found = await repo.get_after_snapshot_no(case_id=case_id, last_seen_no=2)

    assert found == []
