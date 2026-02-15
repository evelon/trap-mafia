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


class RoomStateCode(str, Enum):
    """Purpose
    - room_state SSE payload의 code 필드에 사용됩니다.

    Meaning
    - 방 상태 변화의 원인을 표현하는 이벤트 코드입니다.

    Field interpretation
    - SNAPSHOT_ON_CONNECT: SSE 최초 연결 시 최신 snapshot 전달.
    - ROOM_USER_JOINED: 방에 유저가 입장.
    - ROOM_USER_LEFT: 방에서 유저가 퇴장.
    - ROOM_CASE_START: case 시작으로 current_case.status 변경.
    - ROOM_CASE_END: case 종료로 current_case.status 변경.
    - ROOM_DELETED: 방 삭제.
    """

    SNAPSHOT_ON_CONNECT = "SNAPSHOT_ON_CONNECT"
    ROOM_USER_JOINED = "ROOM_USER_JOINED"
    ROOM_USER_LEFT = "ROOM_USER_LEFT"
    ROOM_CASE_START = "ROOM_CASE_START"
    ROOM_CASE_END = "ROOM_CASE_END"
    ROOM_DELETED = "ROOM_DELETED"


RoomStateResponse = Envelope[RoomSnapshot, RoomStateCode]
