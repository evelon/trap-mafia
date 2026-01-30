from fastapi import FastAPI

from app.api.rest import router as rest_router
from app.realtime.realtime import router as rt_router

app = FastAPI()

app.include_router(rest_router)
app.include_router(rt_router)
