from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.schemas.common.ids import UserId


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

    async def get_list_by_ids(self, user_ids: list[UserId]) -> list[User]:
        query = select(User).where(User.id.in_(user_ids))
        res = await self.db.execute(query)
        return list(res.scalars().all())

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
