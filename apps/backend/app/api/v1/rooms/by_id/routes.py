from fastapi import APIRouter

from app.api.v1.rooms.by_id.actions import router as actions_router

router = APIRouter(prefix="/{room_id}")

router.include_router(actions_router)
