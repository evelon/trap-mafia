from fastapi import APIRouter

from app.api.v1.cases.phases.routes_current import router as phase_router_current

router = APIRouter(prefix="/current")

router.include_router(phase_router_current)
