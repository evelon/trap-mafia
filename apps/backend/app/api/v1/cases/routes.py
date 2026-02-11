from fastapi import APIRouter

from app.api.v1.cases.by_id.routes import router as router_by_id
from app.api.v1.cases.current.routes import router as router_current

router = APIRouter(prefix="/cases", tags=["cases"])

router.include_router(router_current)
router.include_router(router_by_id)
