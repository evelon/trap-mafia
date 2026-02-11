from enum import Enum

from app.schemas.case.action_responses.common_action import (
    ActionConflictCode,
    ActionForbiddenResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.common.envelope import Envelope


class RedVoteSuccessCode(str, Enum):
    OK = "OK"


class RedVoteBadRequestCode(str, Enum):
    INVALID_TARGET_SEAT_NO = "INVALID_TARGET_SEAT_NO"


class RedVoteNotFoundCode(str, Enum):
    TARGET_SEAT_EMPTY = "TARGET_SEAT_EMPTY"


class RedVoteConflictCode(str, Enum):
    NIGHT_REJECTED_SELF_VOTE = "NIGHT_REJECTED_SELF_VOTE"


RedVoteSuccessResponse = Envelope[ActionReceipt, RedVoteSuccessCode]
RedVoteBadRequestResponse = Envelope[None, RedVoteBadRequestCode]
RedVoteNotFoundResponse = Envelope[None, RedVoteNotFoundCode]
RedVoteForbiddenResponse = ActionForbiddenResponse
RedVoteConflictAnyCode = ActionConflictCode | RedVoteConflictCode
RedVoteConflictResponse = Envelope[None, RedVoteConflictAnyCode]
