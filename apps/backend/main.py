from fastapi import FastAPI

from app.api.routes import router as rest_router
from app.core.exception_handler import register_exception_handlers
from app.realtime.routes import router as realtime_router

api = FastAPI()

api.include_router(rest_router)
api.include_router(realtime_router)

register_exception_handlers(api)
