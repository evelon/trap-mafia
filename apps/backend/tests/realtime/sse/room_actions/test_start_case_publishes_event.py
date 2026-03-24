from __future__ import annotations

from typing import Awaitable, Callable

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.events.case import CaseSnapshotType
from app.infra.pubsub.topics import CaseTopic
from app.models.auth import User
from app.models.room import Room
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import CaseStartReason
from app.schemas.room.response import (
    CaseStartConflictCode,
    CaseStartConflictResponse,
    CaseStartResponse,
    CaseStartSuccessCode,
)
from tests._helpers.auth import UserAuth
from tests._helpers.entity import room_with_members
from tests.realtime.sse.room_actions.conftest import FakeCaseEventBus


@pytest.mark.anyio
async def test_case_start_emits_member_joined_event(
    client: AsyncClient,
    user_auth: UserAuth,
    fake_case_bus: FakeCaseEventBus,
    user_hosted_room: Room,
    add_new_user_to_room: Callable[[Room], Awaitable[User]],
) -> None:
    """
    join_room에서 실제로 join이 발생하면, Redis pubsub에는 snapshot이 아니라
    delta event가 publish된다.
    """
    # given
    for _ in range(3):
        await add_new_user_to_room(user_hosted_room)

    # when
    r = await client.post("/api/v1/rooms/current/case-start", json={"red_player_count": None})

    # then
    assert r.status_code == status.HTTP_200_OK, r.text

    envelope = CaseStartResponse.model_validate(r.json())
    assert envelope.ok is True
    assert envelope.code == CaseStartSuccessCode.OK

    mutation = envelope.data
    assert mutation
    assert mutation.target == Target.ROOM
    assert mutation.subject == Subject.CASE
    assert mutation.subject_id is not None
    assert mutation.on_target is True
    assert mutation.changed is True
    assert mutation.reason == CaseStartReason.STARTED

    # 상태 변화가 있었다면 publish 되어야 함
    assert len(fake_case_bus.calls) == 1
    call = fake_case_bus.calls[0]
    assert call.topic == CaseTopic(mutation.subject_id)
    assert call.event.type == CaseSnapshotType.STARTED


@pytest.mark.anyio
async def test_case_start_does_not_emit_when_already_started(
    db_session: AsyncSession,
    client: AsyncClient,
    user_auth: UserAuth,
    fake_case_bus: FakeCaseEventBus,
) -> None:
    """
    이미 방에 들어가 있는 경우(JoinRoomReason.ALREADY_JOINED)에는 상태 변화가 없으므로
    publish하지 않는다.
    """
    # 첫 start -> publish 1회
    await room_with_members(
        db_session, [user_auth["username"], "username3", "username4", "username5"]
    )
    r = await client.post("/api/v1/rooms/current/case-start", json={"red_player_count": None})
    assert len(fake_case_bus.calls) == 1

    # 두 번째 start -> publish 증가 없음
    r = await client.post("/api/v1/rooms/current/case-start", json={"red_player_count": None})
    assert r.status_code == status.HTTP_409_CONFLICT, r.text

    print(r.json())
    envelope = CaseStartConflictResponse.model_validate(r.json())
    assert envelope.ok is False
    assert envelope.code == CaseStartConflictCode.ROOM_CASE_RUNNING
    assert envelope.data is None
    assert len(fake_case_bus.calls) == 1
