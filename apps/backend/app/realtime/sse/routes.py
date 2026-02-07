from fastapi import APIRouter

from app.realtime.sse.cases.routes import router as cases_router
from app.realtime.sse.rooms.routes import router as rooms_router

router = APIRouter(prefix="/sse", tags=["sse"])

router.include_router(cases_router)
router.include_router(rooms_router)
