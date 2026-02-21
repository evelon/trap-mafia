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

    async def create(self, *, username: str) -> User:
        user = User(username=username)
        self.db.add(user)
        return user


def get_user_repo(db: DbSessionDep) -> UserRepo:
    return UserRepo(db)


UserRepoDep = Annotated[UserRepo, Depends(get_user_repo)]
