from enum import Enum


class SSEEventType(str, Enum):
    """Purpose
    - SSE payload의 code 필드에 사용됩니다.

    Field interpretation
    - ON_CONNECT: SSE 최초 연결 시 최신 정보 전달.

    - ROOM_EVENT: room change 일어남.
    - CASE_EVENT: case change 일어남.

    - STREAM_CLOSE: close로 인한 stream 끊기
    """

    ON_CONNECT = "ON_CONNECT"

    ROOM_EVENT = "ROOM_EVENT"
    CASE_EVENT = "CASE_EVENT"

    STREAM_CLOSE = "STREAM_CLOSE"


class SSEEnvelopeCode(str, Enum):
    """
    SSE의 Envelope 유형을 나타냄
    """

    ROOM_STATE = "ROOM_STATE"
    CASE_STATE = "CASE_STATE"

    ROOM_LEAVE = "ROOM_LEAVE"
    ROOM_KICKED = "ROOM_KICKED"

    ROOM_MEMBERSHIP_INVALID = "ROOM_MEMBERSHIP_INVALID"

    STREAM_CLOSE = "STREAM_CLOSE"  # 강제 종료 시 (close api 등)
