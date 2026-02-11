from enum import Enum

from pydantic import BaseModel

from app.domain.types import SeatNo
from app.schemas.common.envelope import Envelope


class CaseResultWinner(str, Enum):
    RED = "RED"
    BLUE = "BLUE"


class CaseResultPlayer(BaseModel):
    seat_no: SeatNo
    team: CaseResultWinner


class CaseResultData(BaseModel):
    winner: CaseResultWinner
    players: list[CaseResultPlayer]


class CaseResultSuccessCode(str, Enum):
    OK = "OK"


CaseResultSuccessResponse = Envelope[CaseResultData, CaseResultSuccessCode]


class CaseResultErrorCode(str, Enum):
    CASE_NOT_FOUND = "CASE_NOT_FOUND"
    CASE_RUNNING = "CASE_RUNNING"


CaseResultErrorResponse = Envelope[None, CaseResultErrorCode]
