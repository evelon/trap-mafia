from fastapi import APIRouter

from app.realtime.v1.sse.cases.current.routes import router as router_current

router = APIRouter(prefix="/cases", tags=["cases"])

router.include_router(router_current)
