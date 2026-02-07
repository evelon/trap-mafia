from fastapi import FastAPI

from app.api.routes import router as rest_router
from app.realtime.routes import router as realtime_router

app = FastAPI()

app.include_router(rest_router)
app.include_router(realtime_router)
