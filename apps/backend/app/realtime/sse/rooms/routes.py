from fastapi import APIRouter

from app.realtime.sse.rooms.room import router as room_router

router = APIRouter(prefix="/rooms", tags=["rooms"])

router.include_router(room_router)
