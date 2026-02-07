from fastapi import APIRouter

from app.api.auth.routes import router as auth_router
from app.api.cases.routes import router as cases_router
from app.api.health import router as health_router
from app.api.rooms.routes import router as rooms_router

router = APIRouter(prefix="/api")

router.include_router(auth_router)
router.include_router(cases_router)
router.include_router(rooms_router)

router.include_router(health_router)
