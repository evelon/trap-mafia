from pydantic import BaseModel

from app.domain.types import SeatNo


class CaseStartRequest(BaseModel):
    red_player_count: SeatNo | None
