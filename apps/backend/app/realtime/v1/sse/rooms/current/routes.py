from fastapi import APIRouter

from app.core.deps.require_in_room import RequireInRoom
from app.realtime.v1.sse.rooms.current.control import router as control_router
from app.realtime.v1.sse.rooms.current.room import router as room_router

router = APIRouter(prefix="/current", dependencies=[RequireInRoom])

router.include_router(control_router)
router.include_router(room_router)
