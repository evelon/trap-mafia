# tests/api/rooms/test_rooms_contract_auth.py
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.error_codes import AuthCommonErrorCode
from app.schemas.room.response import JoinRoomResponse
from tests._helpers.validators import RespValidator, general_failure_validator

join_resp_validator = RespValidator(JoinRoomResponse)


@pytest.mark.api
async def test_rooms_join_requires_auth(db_session: AsyncSession, client: AsyncClient):
    resp = await client.post(f"/api/v1/rooms/{uuid4()}/join")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    env = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env.code == AuthCommonErrorCode.AUTH_UNAUTHORIZED


@pytest.mark.api
async def test_rooms_kick_requires_auth(client: AsyncClient):
    resp = await client.post(f"/api/v1/rooms/current/users/{uuid4()}/kick")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    env = general_failure_validator.assert_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env.code == AuthCommonErrorCode.AUTH_UNAUTHORIZED
