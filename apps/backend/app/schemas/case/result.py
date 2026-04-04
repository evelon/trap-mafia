from enum import Enum

from app.domain.types import SeatNo
from app.schemas.base import RequiredFieldsModel
from app.schemas.common.envelope import Envelope


class CaseResultWinner(str, Enum):
    RED = "RED"
    BLUE = "BLUE"


class CaseResultPlayer(RequiredFieldsModel):
    seat_no: SeatNo
    team: CaseResultWinner


class CaseResultData(RequiredFieldsModel):
    winner: CaseResultWinner
    players: list[CaseResultPlayer]


class CaseResultSuccessCode(str, Enum):
    OK = "OK"


CaseResultSuccessResponse = Envelope[CaseResultData, CaseResultSuccessCode]


class CaseResultErrorCode(str, Enum):
    CASE_NOT_FOUND = "CASE_NOT_FOUND"
    CASE_RUNNING = "CASE_RUNNING"


CaseResultErrorResponse = Envelope[None, CaseResultErrorCode]
