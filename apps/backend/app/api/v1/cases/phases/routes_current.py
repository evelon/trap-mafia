from fastapi import APIRouter

from app.api.v1.cases.phases.actions.routes import router as action_router

router = APIRouter(prefix="/phases", tags=["phases"])

router.include_router(action_router)
