from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Room(Base):
    __tablename__ = "room"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
