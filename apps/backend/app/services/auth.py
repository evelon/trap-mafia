from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EnvelopeException
from app.infra.db.session import DbSessionDep
from app.models.auth import User
from app.repositories.user import UserRepo, UserRepoDep
from app.schemas.common.error import AuthErrorCode, AuthLoginErrorCode


class AuthService:
    def __init__(self, db: AsyncSession, user_repo: UserRepo):
        self.db = db
        self.repo = user_repo

    async def get_or_create_guest_user(self, username: str) -> User:
        """게스트 로그인용 user upsert."""

        user = await self.repo.get_by_username(username)
        if user:
            return user

        user = await self.repo.create(username=username)
        try:
            await self.db.commit()
        except IntegrityError:
            # UNIQUE(username) 레이스: 생성이 먼저 된 경우 재조회
            await self.db.rollback()
            user = await self.repo.get_by_username(username)
            assert user is not None
            return user

        await self.db.refresh(user)
        return user

    async def get_username_by_user_id(self, user_id: str) -> str:
        """
        user_id로 username을 조회한다.

        - 해당 user가 없으면 404 예외를 발생시킨다.
        """
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            # Invalid UUID in token/session payload -> treat as unauthorized.
            raise EnvelopeException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                response_code=AuthErrorCode.AUTH_UNAUTHORIZED,
            )

        query = select(User).where(User.id == user_uuid)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            raise EnvelopeException(
                status_code=status.HTTP_404_NOT_FOUND,
                response_code=AuthLoginErrorCode.AUTH_USER_NOT_FOUND,
            )

        return user.username


def get_auth_service(db: DbSessionDep, user_repo: UserRepoDep) -> AuthService:
    return AuthService(db, user_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
