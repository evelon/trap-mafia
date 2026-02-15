from fastapi import APIRouter

from app.realtime.v1.routes import router as v1_router

router = APIRouter(prefix="/rt", tags=["realtime"])

router.include_router(v1_router)
