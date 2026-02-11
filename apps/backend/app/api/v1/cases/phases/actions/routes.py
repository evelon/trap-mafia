from fastapi import APIRouter

from app.api.v1.cases.phases.actions.blue_vote import router as blue_vote_router
from app.api.v1.cases.phases.actions.force_skip_discuss import router as force_skip_discuss_router
from app.api.v1.cases.phases.actions.init_blue_vote import router as init_blue_vote_router
from app.api.v1.cases.phases.actions.red_vote import router as red_vote_router

router = APIRouter()

router.include_router(blue_vote_router)
router.include_router(force_skip_discuss_router)
router.include_router(init_blue_vote_router)
router.include_router(red_vote_router)
