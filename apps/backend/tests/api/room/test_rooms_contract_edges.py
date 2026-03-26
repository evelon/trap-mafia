from __future__ import annotations

import uuid

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.error_codes import AuthCommonErrorCode, CommonErrorCode
from app.models.room import Room
from app.schemas.room.response import JoinRoomResponse
from tests._helpers.auth import UserAuth
from tests._helpers.validators import RespValidator, general_failure_validator

join_room_validator = RespValidator(JoinRoomResponse)


@pytest.mark.api
async def test_rooms_join_requires_auth(client: AsyncClient):
    """
    rooms 라우터는 router-level auth dependency가 걸려있어야 함.
    (쿠키/토큰 없으면 Envelope(ok=False)로 떨어져야 함)
    """
    resp = await client.post("/api/v1/rooms/current/join")
    assert resp.status_code == 401

    env = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env.code == AuthCommonErrorCode.AUTH_UNAUTHORIZED


@pytest.mark.api
async def test_rooms_kick_requires_auth(client: AsyncClient):
    resp = await client.post(f"/api/v1/rooms/current/users/{uuid.uuid4()}/kick")
    assert resp.status_code == 401

    env = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env.code == AuthCommonErrorCode.AUTH_UNAUTHORIZED


@pytest.mark.api
async def test_rooms_kick_not_in_room_403(client: AsyncClient, user_auth: UserAuth) -> None:
    r = await client.post("/api/v1/rooms/current/users/not-a-uuid/kick")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
async def test_rooms_kick_invalid_uuid_is_enveloped_validation_error(
    client: AsyncClient, user_auth: UserAuth, user_hosted_room: Room
):
    """
    FastAPI validation error까지 Envelope로 감싸는 정책 고정.
    """
    # user_auth로 로그인(쿠키 확보)
    # user_id 자리에 UUID가 아닌 값을 넣어서 422 유도

    # 422
    r2 = await client.post("/api/v1/rooms/current/users/not-a-uuid/kick")
    assert r2.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    env = general_failure_validator.assert_envelope(r2.json(), ok=False, meta_is_null=True)
    assert env.code == CommonErrorCode.VALIDATION_ERROR


@pytest.mark.api
async def test_join_response_does_not_include_case_info_even_if_case_exists(
    client: AsyncClient, user_auth: UserAuth, random_room: Room
):
    """
    정책:
    - room REST(join)은 running case를 조회/접근하지 않는다.
    - 따라서 join 응답 data는 JoinRoomMutation만 포함하며,
      case 관련 필드(예: case_id, redirect_to 등)는 포함하지 않는다.
    """
    # 로그인

    # join
    resp = await client.post(f"/api/v1/rooms/{random_room.id}/join")
    assert resp.status_code == 200

    env = join_room_validator.assert_envelope(resp.json(), ok=True, meta_is_null=True)

    # JoinRoomMutation의 핵심 키들만 기대 (너희 스키마 기준)
    # - target, subject, subject_id, on_target, changed, reason

    # case 관련 정보가 섞이지 않는지 (방어적 체크)
    forbidden = {"case_id", "current_case_id", "redirect_to", "case", "case_state", "running_case"}
    assert forbidden.isdisjoint(set(env.data.__dict__.keys()))
