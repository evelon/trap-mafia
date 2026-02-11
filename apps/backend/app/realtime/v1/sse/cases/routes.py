from fastapi import APIRouter

from app.realtime.v1.sse.cases.case import router as case_router

router = APIRouter(prefix="/cases", tags=["cases"])

router.include_router(case_router)
