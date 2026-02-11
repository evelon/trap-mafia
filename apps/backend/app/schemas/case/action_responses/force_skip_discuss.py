from __future__ import annotations

from enum import Enum

from app.schemas.case.action_responses.common_action import (
    ActionConflictResponse,
    ActionForbiddenResponse,
)
from app.schemas.case.actions.common import ActionReceipt
from app.schemas.common.envelope import Envelope


class ForceSkipDiscussSuccessCode(str, Enum):
    OK = "OK"


ForceSkipDiscussSuccessResponse = Envelope[ActionReceipt, ForceSkipDiscussSuccessCode]
ForceSkipDiscussForbiddenResponse = ActionForbiddenResponse
ForceSkipDiscussConflictResponse = ActionConflictResponse
