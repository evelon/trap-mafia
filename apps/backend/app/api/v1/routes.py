from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.cases.routes import router as cases_router
from app.api.v1.rooms.routes import router as rooms_router

router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(cases_router)
router.include_router(rooms_router)
