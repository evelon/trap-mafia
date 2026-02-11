from fastapi import APIRouter

from app.api.cases.phases.action import router as action_router

router = APIRouter(prefix="/current/phases", tags=["phases"])

router.include_router(action_router)
