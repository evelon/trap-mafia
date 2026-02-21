from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import JwtHandler
from app.models.auth import User
from tests._helpers.envelope_assert import assert_is_envelope


@pytest.mark.api
@pytest.mark.asyncio
async def test_guest_login_sets_access_refresh_as_verifiable_jwt(
    client, jwt_test_handler: JwtHandler, db_session: AsyncSession
):
    username = "tester_jwt"
    resp = await client.post("/api/v1/auth/guest-login", json={"username": username})
    assert resp.status_code == 200
    assert_is_envelope(resp.json(), ok=True, meta_is_null=True)

    access = resp.cookies.get("access_token")
    refresh = resp.cookies.get("refresh_token")
    assert isinstance(access, str) and access.count(".") == 2
    assert isinstance(refresh, str) and refresh.count(".") == 2
    query = select(User).where(User.username == username)
    res = await db_session.execute(query)
    user = res.scalar_one()

    claims_access = jwt_test_handler.decode_and_verify(access)
    claims_refresh = jwt_test_handler.decode_and_verify(refresh)

    assert claims_access["typ"] == "access"
    assert claims_access["sub"] == str(user.id)

    assert claims_refresh["typ"] == "refresh"
    assert claims_refresh["sub"] == str(user.id)
    assert "jti" in claims_refresh
