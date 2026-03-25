from fastapi import APIRouter

from app.realtime.v1.sse.cases.current.state import router as phase_router_current

router = APIRouter(prefix="/current")

router.include_router(phase_router_current)
