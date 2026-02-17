from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import DbSession
from app.services.redis import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: DbSession):
    # DB ping
    await db.execute(text("SELECT 1"))

    # Redis ping (optional)
    await redis_client.ping()

    return {"ok": True}
