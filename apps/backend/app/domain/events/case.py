from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.common.ids import PhaseId


class CaseSnapshotType(str, Enum):
    ON_CONNECT = "case.connected"
    STARTED = "case.start"
    NIGHT = "case.night"
    DISCUSS_AFTER_NIGHT = "case.discuss.after_night"
    VOTE = "case.vote"
    DISCUSS_AFTER_VOTE = "case.disucss.after_vote"
    ENDED = "case.ended"
    INTERRUPTED = "case.interrupted"


class CaseEventDelta(BaseModel):
    type: CaseSnapshotType  # 부가
    phase_id: PhaseId  # 부가
    ts: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone.utc))]
    snapshot_no: int  # 실제 snapshot 가져오는 id
