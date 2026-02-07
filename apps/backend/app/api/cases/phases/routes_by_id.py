from fastapi import APIRouter

router = APIRouter(prefix="/{case_id}/phases", tags=["phases"])
