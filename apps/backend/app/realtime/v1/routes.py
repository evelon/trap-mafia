from fastapi import APIRouter

from app.realtime.v1.sse.routes import router as sse_router
from app.realtime.v1.ws.routes import router as ws_router

router = APIRouter(prefix="/v1", tags=["v1"])

router.include_router(sse_router)
router.include_router(ws_router)
