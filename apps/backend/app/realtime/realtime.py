from fastapi import APIRouter

from app.realtime.sse import router as sse_router
from app.realtime.ws import router as ws_router

router = APIRouter(prefix="/rt")

router.include_router(sse_router, tags=["realtime"])
router.include_router(ws_router, tags=["realtime"])
