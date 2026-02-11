from enum import Enum

from app.schemas.common.envelope import Envelope


class ActionForbiddenCode(str, Enum):
    """
    Action API 공통 403 코드.

    의미:
    - room/case 컨텍스트 자체가 없는 상태에서 action을 시도한 경우에 사용한다.
    """

    PERMISSION_DENIED_NOT_IN_ROOM = "PERMISSION_DENIED_NOT_IN_ROOM"
    PERMISSION_DENIED_NOT_IN_CASE = "PERMISSION_DENIED_NOT_IN_CASE"


class ActionConflictCode(str, Enum):
    """
    Action API 공통 409 코드.

    의미:
    - 동일한 room/case/phase 컨텍스트 안에서 상태와 충돌하는 action을 시도한 경우에 사용한다.
    """

    PHASE_REJECTED_ALREADY_DECIDED = "PHASE_REJECTED_ALREADY_DECIDED"
    PHASE_REJECTED_CONFLICT_ACTION = "PHASE_REJECTED_CONFLICT_ACTION"


ActionForbiddenResponse = Envelope[None, ActionForbiddenCode]
ActionConflictResponse = Envelope[None, ActionConflictCode]
