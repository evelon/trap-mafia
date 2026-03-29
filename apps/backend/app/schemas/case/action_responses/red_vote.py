from enum import Enum

from app.core.error_codes import BadRequestErrorCode, ConflictErrorCode, PermissionErrorCode
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.common.envelope import Envelope


class RedVoteSuccessCode(str, Enum):
    OK = "OK"


RedVoteSuccessResponse = Envelope[ActionReceipt, RedVoteSuccessCode]
RedVoteBadRequestResponse = Envelope[None, BadRequestErrorCode]
RedVoteForbiddenResponse = Envelope[None, PermissionErrorCode]
RedVoteConflictResponse = Envelope[None, ConflictErrorCode]
