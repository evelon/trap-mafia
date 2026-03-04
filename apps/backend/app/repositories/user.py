from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.session import DbSessionDep
from app.models.auth import User


class UserRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def get_by_id(self, user_id) -> User | None:
        """Return user by id or None."""
        query = select(User).where(User.id == user_id)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def ensure_exists(self, user_id) -> None:
        """Ensure user exists, otherwise raise EntityNotFoundError."""
        from app.domain.exceptions import EntityNotFoundError

        user = await self.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)

    async def create(self, *, username: str) -> User:
        user = User(username=username)
        self.db.add(user)
        return user


def get_user_repo(db: DbSessionDep) -> UserRepo:
    return UserRepo(db)


UserRepoDep = Annotated[UserRepo, Depends(get_user_repo)]
