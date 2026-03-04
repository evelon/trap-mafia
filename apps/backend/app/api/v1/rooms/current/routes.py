from fastapi import APIRouter

from app.api.v1.rooms.current.actions import router as actions_router
from app.api.v1.rooms.current.users.routes import router as user_by_id_router

router = APIRouter(prefix="/current")

router.include_router(actions_router)
router.include_router(user_by_id_router)
