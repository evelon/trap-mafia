from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as rest_router
from app.core.exception_handler import register_exception_handlers
from app.core.middleware import register_middlewares
from app.infra.db.engine import get_sessionmaker
from app.mvp import create_mvp_lifespan
from app.realtime.routes import router as realtime_router


def create_app(*, lifespan=None) -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # TODO: 프론트 cors 임시 대응. 추후 수정 필요
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # TODO: 프론트 cors 임시 대응. 추후 수정 필요
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(rest_router)
    app.include_router(realtime_router)

    register_middlewares(app)
    register_exception_handlers(app)

    return app


mvp_lifespan = create_mvp_lifespan(get_sessionmaker())

api = create_app(lifespan=mvp_lifespan)
