from fastapi import APIRouter

from app.api.v1.rooms.current.users.by_id import router as router_by_id

router = APIRouter(prefix="/users")

router.include_router(router_by_id)
