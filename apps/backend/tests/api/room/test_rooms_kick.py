from __future__ import annotations

import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.room import RoomMember
from app.schemas.common.error import CommonErrorCode
from app.schemas.common.mutation import Subject, Target
from app.schemas.room.mutation import KickUserReason
from app.schemas.room.response import KickUserResponse
from tests._helpers.auth import UserAuth
from tests._helpers.entity import create_room, create_user
from tests._helpers.validators import RespValidator, general_failure_validator

kick_resp_validator = RespValidator(KickUserResponse)


async def _add_active_membership(
    db: AsyncSession, *, room_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    db.add(RoomMember(room_id=room_id, user_id=user_id))
    await db.commit()


@pytest.mark.api
async def test_kick_user_success_returns_kicked(
    client: AsyncClient, db_session: AsyncSession, user_auth: UserAuth
):
    """
    POST /api/v1/rooms/current/users/{user_id}/kick
    - 대상이 어떤 room에든 active membership이 있으면 kick 성공
    - 200 + Envelope(ok=True)
    - data.reason == KICKED, changed == True
    """
    # actor 로그인(쿠키 확보)
    actor_id = user_auth["id"]
    # target 유저 + room + target membership 준비(DB 직접)
    target_id = await create_user(db_session, username="api_kick_target")
    room_id = await create_room(db_session, host_id=actor_id)
    await _add_active_membership(db_session, room_id=room_id, user_id=target_id)

    # kick
    resp = await client.post(f"/api/v1/rooms/current/users/{target_id}/kick")
    assert resp.status_code == 200

    env = kick_resp_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)

    data = env.data
    assert data is not None
    # Mutation 계약
    assert data.target == Target.ROOM
    assert data.subject == Subject.USER
    assert data.subject_id == target_id
    assert data.on_target is False
    assert data.changed is True
    assert data.reason == KickUserReason.KICKED


@pytest.mark.api
async def test_kick_user_idempotent_when_target_not_in_room(
    client: AsyncClient, db_session: AsyncSession, user_auth: UserAuth
):
    """
    - target이 active membership이 없으면 멱등
    - 200 + Envelope(ok=True)
    - data.reason == NOT_IN_ROOM, changed == False
    """
    # actor 로그인

    # target 유저만 만들고 membership은 만들지 않음
    target_id = await create_user(db_session, username="api_kick_target2")

    resp = await client.post(f"/api/v1/rooms/current/users/{target_id}/kick")
    assert resp.status_code == 200

    env = kick_resp_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)
    data = env.data

    assert data is not None
    assert data.target == Target.ROOM
    assert data.subject == Subject.USER
    assert data.subject_id == target_id
    assert data.on_target is False
    assert data.changed is False
    assert data.reason == KickUserReason.NOT_IN_ROOM


@pytest.mark.api
async def test_kick_returns_user_not_found_when_target_user_missing(
    client: AsyncClient, user_auth: UserAuth
):
    """
    계약:
    - target_user_id가 User 테이블에 없으면
      - NOT_IN_ROOM 멱등으로 처리하지 말고
      - USER_NOT_FOUND 류의 에러로 응답한다.
    """
    # user_auth로 actor 로그인(쿠키)

    missing_user_id = uuid.uuid4()

    resp = await client.post(f"/api/v1/rooms/current/users/{missing_user_id}/kick")

    # 너희 정책에 맞춰 하나로 고정하면 됨 (보통 404가 자연스러움)
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    env = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)

    # 프로젝트에 이미 있는 코드로 맞춰줘.
    # (예: USER_NOT_FOUND / AUTH_USER_NOT_FOUND / RESOURCE_NOT_FOUND 등)
    assert env.code == CommonErrorCode.NOT_FOUND
