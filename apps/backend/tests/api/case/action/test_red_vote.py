import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import PhaseType
from app.models.case import Phase
from app.models.case_snapshot import CaseSnapshotHistory
from app.repositories.case_player import CasePlayerRepo
from app.services.case import CaseService
from tests._helpers.auth import UserAuth
from tests._helpers.entity import room_with_members
from tests.conftest import FakePubSub


@pytest.mark.anyio
async def test_red_vote_does_not_create_snapshot_or_emit(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    # given
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, user_ids = await room_with_members(db_session, usernames)

    # start case
    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id
    published_before = len(fake_pubsub.published)

    # snapshot count before
    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1  # initial snapshot

    # when: red vote 1회
    all_players = await case_player_repo.list_by_case_id(case_id=case_id)
    other_players = [player for player in all_players if player.user_id != user_auth["id"]]
    target_seat_no = other_players[1].seat_no

    vote_res = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": str(target_seat_no)},
    )
    # then
    assert vote_res.status_code == 200

    # snapshot unchanged
    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    # no pubsub emit
    assert published_before == len(fake_pubsub.published)


@pytest.mark.anyio
async def test_red_vote_skip_does_not_create_snapshot_or_emit(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    # given
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _user_ids = await room_with_members(db_session, usernames)

    mut = await case_service.start_case(room_id)
    _case_id = mut.subject_id
    published_before = len(fake_pubsub.published)

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    assert before_count == 1

    # when: skip 1회
    vote_res = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": None},
    )

    # then
    assert vote_res.status_code == status.HTTP_200_OK

    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    assert published_before == len(fake_pubsub.published)


@pytest.mark.anyio
async def test_red_vote_fails_on_self_vote(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _user_ids = await room_with_members(db_session, usernames)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    players = await case_player_repo.list_by_case_id(case_id=case_id)
    my_seat_no = [player.seat_no for player in players if player.user_id == user_auth["id"]][0]

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    before_publish_count = len(fake_pubsub.published)

    res = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": my_seat_no},
    )

    assert res.status_code == status.HTTP_409_CONFLICT

    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    assert len(fake_pubsub.published) == before_publish_count


@pytest.mark.anyio
async def test_red_vote_fails_on_invalid_target_seat(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _user_ids = await room_with_members(db_session, usernames)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    players = await case_player_repo.list_by_case_id(case_id=case_id)
    invalid_seat_no = len(players)

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    before_publish_count = len(fake_pubsub.published)

    res = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": invalid_seat_no},
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST

    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    assert len(fake_pubsub.published) == before_publish_count


@pytest.mark.anyio
async def test_red_vote_fails_on_duplicate_action(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    # given
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _user_ids = await room_with_members(db_session, usernames)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    all_players = await case_player_repo.list_by_case_id(case_id=case_id)
    other_players = [player for player in all_players if player.user_id != user_auth["id"]]
    target_seat_no = other_players[1].seat_no

    first = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": target_seat_no},
    )
    assert first.status_code == status.HTTP_200_OK

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    before_publish_count = len(fake_pubsub.published)

    # when
    second = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": target_seat_no},
    )

    # then
    assert second.status_code == status.HTTP_409_CONFLICT

    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    assert len(fake_pubsub.published) == before_publish_count


@pytest.mark.anyio
async def test_red_vote_fails_when_actor_is_not_alive(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    case_player_repo: CasePlayerRepo,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _user_ids = await room_with_members(db_session, usernames)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    players = await case_player_repo.list_by_case_id(case_id=case_id)
    me = [player for player in players if player.user_id == user_auth["id"]][0]
    target = [player for player in players if player.user_id != user_auth["id"]][0]

    me.life_left = 0
    await db_session.commit()

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    before_publish_count = len(fake_pubsub.published)

    res = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": target.seat_no},
    )

    assert res.status_code == status.HTTP_409_CONFLICT

    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    assert len(fake_pubsub.published) == before_publish_count


@pytest.mark.anyio
async def test_red_vote_fails_when_not_night_phase(
    client: AsyncClient,
    user_auth: UserAuth,
    case_service: CaseService,
    db_session: AsyncSession,
    fake_pubsub: FakePubSub,
):
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _user_ids = await room_with_members(db_session, usernames)

    mut = await case_service.start_case(room_id)
    case_id = mut.subject_id

    result = await db_session.execute(
        select(Phase).where(Phase.case_id == case_id, Phase.closed_at.is_(None))
    )
    phase = result.scalar_one()
    phase.phase_type = PhaseType.DISCUSS
    await db_session.commit()

    result = await db_session.execute(select(CaseSnapshotHistory))
    before_count = len(result.scalars().all())
    before_publish_count = len(fake_pubsub.published)

    res = await client.post(
        "/api/v1/cases/current/phases/current/red-vote",
        json={"target_seat_no": 1},
    )

    assert res.status_code == status.HTTP_409_CONFLICT

    result = await db_session.execute(select(CaseSnapshotHistory))
    after_count = len(result.scalars().all())
    assert after_count == before_count

    assert len(fake_pubsub.published) == before_publish_count
