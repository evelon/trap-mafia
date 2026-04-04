from pydantic import Field

from app.domain.types import SeatNo
from app.schemas.base import RequiredFieldsModel


class CaseStartRequest(RequiredFieldsModel):
    red_player_count: SeatNo | None = Field(default=None)
