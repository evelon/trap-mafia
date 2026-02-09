from fastapi import APIRouter

from app.api.v1.auth.session import router as session_router

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(session_router)
