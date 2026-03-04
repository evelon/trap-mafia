from fastapi import APIRouter

from app.api.v1.rooms.by_id.routes import router as router_by_id
from app.api.v1.rooms.current.routes import router as router_current
from app.core.security.auth import RequireAuthentication

router = APIRouter(prefix="/rooms", tags=["rooms"], dependencies=[RequireAuthentication])

router.include_router(router_current)
router.include_router(router_by_id)
