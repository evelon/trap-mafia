from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field


class ActionReceipt(BaseModel):
    """
    공통 Action Receipt.

    의미:
    - Action API가 서버에 의해 "접수(accepted)" 되었음을 나타낸다.
    - 실제 상태 변화(스냅샷)는 SSE(case_state)로 확인한다.

    필드 해석:
    - action_id: 동일 case 내에서 단조 증가하는 action 식별자(1..)
    - phase_id: action이 접수된 시점의 phase 식별자(UUID)
    - accepted_at: 서버가 action을 접수한 시각(UTC, ISO 8601)
    """

    action_id: int = Field(ge=1, description="Action id (1..).")
    phase_id: UUID = Field(description="Phase id (uuid).")
    accepted_at: datetime = Field(description="Accepted at (UTC).")

    @classmethod
    def mock(cls, *, action_id: int = 1, phase_id: UUID | None = None) -> "ActionReceipt":
        """
        테스트/목업용 ActionReceipt 생성.

        의미:
        - DB 없이도 응답 스키마를 검증할 수 있도록 최소 값으로 생성한다.
        """
        if phase_id is None:
            phase_id = UUID("00000000-0000-0000-0000-000000000001")
        return cls(
            action_id=action_id,
            phase_id=phase_id,
            accepted_at=datetime.now(timezone.utc),
        )
