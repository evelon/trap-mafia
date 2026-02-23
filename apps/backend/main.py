from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as rest_router
from app.core.exception_handler import register_exception_handlers
from app.realtime.routes import router as realtime_router

api = FastAPI()

# TODO: 프론트 cors 임시 대응. 추후 수정 필요
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(rest_router)
api.include_router(realtime_router)

register_exception_handlers(api)
