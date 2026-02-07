from fastapi import APIRouter

from app.realtime.sse.routes import router as sse_router
from app.realtime.ws.routes import router as ws_router

router = APIRouter(prefix="/rt", tags=["realtime"])

router.include_router(sse_router)
router.include_router(ws_router)
