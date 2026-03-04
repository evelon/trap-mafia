from fastapi import APIRouter

from app.core.security.auth import RequireAuthentication
from app.realtime.v1.sse.cases.routes import router as cases_router
from app.realtime.v1.sse.rooms.routes import router as rooms_router

router = APIRouter(prefix="/sse", tags=["sse"], dependencies=[RequireAuthentication])

router.include_router(cases_router)
router.include_router(rooms_router)
