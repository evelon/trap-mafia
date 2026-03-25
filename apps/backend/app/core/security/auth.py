from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request, status
from sqlalchemy import select

from app.core.error_codes import AuthCommonErrorCode, AuthUserErrorCode
from app.core.exceptions import EnvelopeHTTPException
from app.core.security.jwt import ACCESS_TOKEN, JwtHandlerDep
from app.domain.types import AuthUser
from app.infra.db.session import DbSessionDep
from app.models.auth import User


async def get_current_user(
    request: Request,
    jwt_handler: JwtHandlerDep,
    db: DbSessionDep,
) -> AuthUser:
    token = request.cookies.get(ACCESS_TOKEN)
    if not token:
        raise EnvelopeHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=AuthCommonErrorCode.AUTH_UNAUTHORIZED,
        )

    claims = jwt_handler.decode_and_verify(token)

    user_id = claims["sub"]

    try:
        user_id = UUID(user_id)
    except ValueError:
        # Invalid UUID in token/session payload -> treat as unauthorized.
        raise EnvelopeHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=AuthCommonErrorCode.AUTH_UNAUTHORIZED,
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise EnvelopeHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=AuthUserErrorCode.AUTH_USER_NOT_FOUND,
        )

    return AuthUser(id=user.id, username=user.username)


RequireAuthentication = Depends(get_current_user)
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
