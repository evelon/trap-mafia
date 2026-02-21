from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.infra.db.session import DbSession
from app.infra.redis import RedisClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: DbSession, redis_client: RedisClient):
    # DB ping
    await db.execute(text("SELECT 1"))

    # Redis ping (optional)
    await redis_client.ping()

    return {"ok": True}
