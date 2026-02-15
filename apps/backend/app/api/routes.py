from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.v1.routes import router as v1_router

router = APIRouter(prefix="/api")

router.include_router(v1_router, tags=["v1"])

router.include_router(health_router)
