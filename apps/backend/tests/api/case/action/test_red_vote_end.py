import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.case_snapshot import CaseSnapshotHistory
from app.repositories.case_player import CasePlayerRepo
from app.services.case import CaseService
from tests._helpers.entity import room_with_members
from tests.conftest import FakePubSub


@pytest.mark.skip(
    reason="multi-player authenticated API flow for red_vote end-to-end is not implemented yet"
)
@pytest.mark.anyio
async def test_red_vote_last_vote_triggers_phase_and_snapshot(
    client: AsyncClient,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    room_id, _user_ids = await room_with_members(db_session)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1

    players = await case_player_repo.list_by_case_id(case_id=case_id)

    # TODO:
    # 각 플레이어의 인증된 API 요청을 보낼 수 있는 fixture가 준비되면
    # 마지막 red_vote까지 수행하고 phase/snapshot/pubsub 변화를 검증한다.
    assert len(players) >= 4


@pytest.mark.skip(
    reason="multi-player authenticated API flow for red_vote end-to-end is not implemented yet"
)
@pytest.mark.anyio
async def test_red_vote_partial_votes_do_not_end_night(
    client: AsyncClient,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    room_id, _user_ids = await room_with_members(db_session)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1

    players = await case_player_repo.list_by_case_id(case_id=case_id)

    # TODO:
    # 일부 플레이어만 인증된 API로 red_vote를 호출하고
    # snapshot/phase/pubsub 변화가 없는지 검증한다.
    assert len(players) >= 2
