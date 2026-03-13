"""room/sse_response.py

Purpose
- room_state SSE 전용 응답 스키마 및 code enum 정의.

Meaning
- RoomStateCode: room_state 이벤트에서 사용되는 도메인 이벤트 코드 집합.
- RoomStateResponse: Envelope 기반의 SSE payload 타입.

Field interpretation
- 실제 SSE 프레임의 event/id/retry는 전송 계층에서 처리합니다.
- 본 스키마는 data(JSON payload) 구조만 정의합니다.
"""

from enum import Enum

from app.schemas.common.envelope import Envelope
from app.schemas.room.state import RoomSnapshot
from app.schemas.sse.response import SSEEnvelopeCode


class RoomEventCode(str, Enum):
    ROOM_STATE = "ROOM_STATE"


RoomStateEnvelope = Envelope[RoomSnapshot, SSEEnvelopeCode]
