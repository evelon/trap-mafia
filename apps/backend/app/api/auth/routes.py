from fastapi import APIRouter

from app.api.auth.session import router as session_router

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(session_router)
