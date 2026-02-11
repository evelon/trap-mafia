from enum import Enum

from app.schemas.case.action_responses.common_action import (
    ActionConflictCode,
    ActionForbiddenResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.common.envelope import Envelope


class InitBlueVoteSuccessCode(str, Enum):
    OK = "OK"


class InitBlueVoteBadRequestCode(str, Enum):
    INVALID_TARGET_SEAT_NO = "INVALID_TARGET_SEAT_NO"


class InitBlueVoteNotFoundCode(str, Enum):
    TARGET_SEAT_EMPTY = "TARGET_SEAT_EMPTY"


class InitBlueVoteConflictCode(str, Enum):
    DISCUSS_REJECTED_NO_TOKEN_INIT = "DISCUSS_REJECTED_NO_TOKEN_INIT"
    DISCUSS_REJECTED_SELF_VOTE_INIT = "DISCUSS_REJECTED_SELF_VOTE_INIT"


InitBlueVoteSuccessResponse = Envelope[ActionReceipt, InitBlueVoteSuccessCode]
InitBlueVoteBadRequestResponse = Envelope[None, InitBlueVoteBadRequestCode]
InitBlueVoteForbiddenResponse = ActionForbiddenResponse
InitBlueVoteNotFoundResponse = Envelope[None, InitBlueVoteNotFoundCode]
InitBlueVoteConflictAnyCode = ActionConflictCode | InitBlueVoteConflictCode
InitBlueVoteConflictResponse = Envelope[None, InitBlueVoteConflictAnyCode]
