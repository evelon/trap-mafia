from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import ACCESS_TOKEN, REFRESH_TOKEN, JwtHandler
from app.models.auth import User
from tests._helpers.auth import UserAuth


@pytest.mark.api
async def test_guest_login_sets_access_refresh_as_verifiable_jwt(
    client: AsyncClient, jwt_test_handler: JwtHandler, db_session: AsyncSession, user_auth: UserAuth
):
    access = user_auth["access_token"]
    refresh = user_auth["refresh_token"]
    username = user_auth["username"]
    assert isinstance(access, str) and access.count(".") == 2
    assert isinstance(refresh, str) and refresh.count(".") == 2
    query = select(User).where(User.username == username)
    res = await db_session.execute(query)
    user = res.scalar_one()

    claims_access = jwt_test_handler.decode_and_verify(access, ACCESS_TOKEN)
    claims_refresh = jwt_test_handler.decode_and_verify(refresh, REFRESH_TOKEN)

    assert claims_access["typ"] == "access"
    assert claims_access["sub"] == str(user.id)

    assert claims_refresh["typ"] == "refresh"
    assert claims_refresh["sub"] == str(user.id)
    assert "jti" in claims_refresh
