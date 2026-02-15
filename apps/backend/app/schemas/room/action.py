from pydantic import BaseModel, Field

from app.domain.types import SeatNo


class CaseStartRequest(BaseModel):
    red_player_count: SeatNo | None = Field(default=None)
