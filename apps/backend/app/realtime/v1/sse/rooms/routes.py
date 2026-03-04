from fastapi import APIRouter

from app.realtime.v1.sse.rooms.current.routes import router as router_current

router = APIRouter(prefix="/rooms", tags=["rooms"])

router.include_router(router_current)
