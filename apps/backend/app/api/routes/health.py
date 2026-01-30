from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.redis import redis_client

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    # DB ping
    db.execute(text("SELECT 1"))

    # Redis ping (optional)
    redis_client.ping()

    return {"ok": True}
