from fastapi import APIRouter

from app.api.v1.cases.phases.action import router as action_router

router = APIRouter(prefix="/current/phases", tags=["phases"])

router.include_router(action_router)
