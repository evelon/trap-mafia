import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.events.case import CaseEventDelta, CaseSnapshotType
from app.infra.pubsub.topics import CaseTopic
from app.models.case import Case
from app.models.case_snapshot import CaseSnapshotHistory
from app.schemas.case.state import CaseSnapshot
from app.schemas.room.mutation import CaseStartMutation
from app.schemas.room.response import CaseStartResponse
from tests._helpers.auth import UserAuth
from tests._helpers.entity import room_with_members
from tests._helpers.validators import RespValidator
from tests.conftest import FakePubSub


@pytest.mark.anyio
async def test_start_case_success(
    db_session: AsyncSession, client: AsyncClient, user_auth: UserAuth
):
    # given
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, users = await room_with_members(db_session, usernames)

    # host가 room creator라고 가정 (fixture 구조에 맞춰 수정 가능)
    # when
    response = await client.post(
        "/api/v1/rooms/current/case-start", json={"red_player_count": None}
    )

    # then
    assert response.status_code == status.HTTP_200_OK

    envelope_validator = RespValidator(CaseStartResponse)
    body = response.json()
    case_start_envelope = envelope_validator.assert_envelope(body)

    # envelope 기본 검증 (네 구조에 맞게 수정 가능)
    assert case_start_envelope.ok is True
    mutation = case_start_envelope.data
    assert mutation is not None

    # DB side-effect 확인

    result1 = await db_session.execute(select(Case))
    case = result1.scalars().first()

    assert case is not None

    case_start_mutation = CaseStartMutation(subject_id=case.id)
    assert mutation.target == case_start_mutation.target
    assert mutation.subject == case_start_mutation.subject
    assert mutation.subject_id == case_start_mutation.subject_id
    assert mutation.on_target == case_start_mutation.on_target
    assert mutation.changed == case_start_mutation.changed

    assert case is not None
    assert case.room_id == room_id

    result2 = await db_session.execute(select(CaseSnapshotHistory))
    history = result2.scalars().first()

    assert history is not None
    snapshot_json = history.snapshot_json
    _ = CaseSnapshot.model_validate(snapshot_json)


# MPV skip: host 권한을 확인하지 않음.
@pytest.mark.skip
@pytest.mark.anyio
async def test_start_case_forbidden_when_not_host(
    db_session: AsyncSession,
    client2: AsyncClient,
    user_auth: UserAuth,
    user_auth2: UserAuth,
):
    # given
    usernames = [user_auth["username"], user_auth2["username"], "username4", "username5"]
    room_id, users = await room_with_members(db_session, usernames)

    # when (non-host가 요청)
    response = await client2.post(
        f"/api/v1/rooms/{room_id}/case-start",
    )

    # then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_start_case_fails_when_already_running(
    db_session: AsyncSession,
    client: AsyncClient,
    client2: AsyncClient,
    user_auth: UserAuth,
):
    # given
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    login_path = "/api/v1/auth/guest-login"
    _ = [await client2.post(login_path, json={"username": username}) for username in usernames]
    _, _ = await room_with_members(db_session, usernames)

    # 첫 번째 start
    response1 = await client.post(
        "/api/v1/rooms/current/case-start", json={"red_player_count": None}
    )
    assert response1.status_code == status.HTTP_200_OK

    # when (두 번째 start)
    response2 = await client.post(
        "/api/v1/rooms/current/case-start", json={"red_player_count": None}
    )

    # then
    assert response2.status_code == status.HTTP_409_CONFLICT


@pytest.mark.anyio
async def test_start_case_not_found_room(
    client: AsyncClient,
    user_auth: UserAuth,
):
    import uuid

    fake_room_id = uuid.uuid4()

    response = await client.post(
        f"/api/v1/rooms/{fake_room_id}/case-start",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_start_case_publishes_case_event(
    db_session: AsyncSession,
    app,
    client: AsyncClient,
    user_auth: UserAuth,
    fake_pubsub: FakePubSub,
):
    # given
    usernames = [user_auth["username"], "username3", "username4", "username5"]
    room_id, _ = await room_with_members(db_session, usernames)

    # pubsub dependency override 필요하면 여기서 연결
    # (이미 fake_pubsub fixture가 override를 해주고 있으면 생략)

    # when
    response = await client.post(
        "/api/v1/rooms/current/case-start",
        json={"red_player_count": None},
    )

    # then
    assert response.status_code == status.HTTP_200_OK
    assert len(fake_pubsub.published) == 1

    case_start_response = CaseStartResponse.model_validate(response.json())
    assert case_start_response.data
    case_id = case_start_response.data.subject_id

    published = fake_pubsub.published[0]
    assert published.topic == CaseTopic(case_id)

    case_event_delta = CaseEventDelta.model_validate_json(published.message)
    assert case_event_delta.type == CaseSnapshotType.STARTED
    assert case_event_delta.snapshot_no == 1
