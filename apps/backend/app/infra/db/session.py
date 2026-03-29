from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.engine import get_sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_sessionmaker()() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
