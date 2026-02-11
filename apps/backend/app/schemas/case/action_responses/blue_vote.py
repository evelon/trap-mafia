from enum import Enum

from app.schemas.case.action_responses.common_action import (
    ActionConflictCode,
    ActionForbiddenResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.common.envelope import Envelope


class BlueVoteSuccessCode(str, Enum):
    OK = "OK"


class BlueVoteConflictCode(str, Enum):
    VOTE_REJECTED_NO_TOKEN = "VOTE_REJECTED_NO_TOKEN"


BlueVoteSuccessResponse = Envelope[ActionReceipt, BlueVoteSuccessCode]
BlueVoteConflictAnyCode = ActionConflictCode | BlueVoteConflictCode
BlueVoteForbiddenResponse = ActionForbiddenResponse
BlueVoteConflictResponse = Envelope[None, BlueVoteConflictAnyCode]
