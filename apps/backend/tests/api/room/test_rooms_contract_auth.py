# tests/api/rooms/test_rooms_contract_auth.py
from __future__ import annotations

import uuid

import pytest
from fastapi import status

from app.mvp import MVP_ROOM_ID
from app.schemas.common.error import AuthErrorCode
from tests._helpers.envelope_assert import assert_is_envelope


@pytest.mark.api
async def test_rooms_join_requires_auth(client):
    resp = await client.post(f"/api/v1/rooms/{MVP_ROOM_ID}/join")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env["code"] == AuthErrorCode.AUTH_UNAUTHORIZED


@pytest.mark.api
async def test_rooms_kick_requires_auth(client):
    resp = await client.post(f"/api/v1/rooms/current/users/{uuid.uuid4()}/kick")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    env = assert_is_envelope(resp.json(), ok=False, meta_is_null=True)
    assert env["code"] == AuthErrorCode.AUTH_UNAUTHORIZED
