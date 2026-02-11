from fastapi import APIRouter

from app.api.v1.cases.phases.routes_by_id import router as phase_router_by_id

router = APIRouter(prefix="/{case_id}")

router.include_router(phase_router_by_id)
