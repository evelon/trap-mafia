from enum import Enum

from app.schemas.common.envelope import Envelope
from app.schemas.room.mutation import (
    CaseStartMutation,
    JoinRoomMutation,
    KickUserMutation,
    LeaveRoomCode,
    LeaveRoomMutation,
)


class JoinRoomCode(str, Enum):
    OK = "OK"


JoinRoomResponse = Envelope[JoinRoomMutation, JoinRoomCode]


LeaveRoomResponse = Envelope[LeaveRoomMutation, LeaveRoomCode]


class KickUserCode(str, Enum):
    OK = "OK"


KickUserResponse = Envelope[KickUserMutation, KickUserCode]


class CaseStartSuccessCode(str, Enum):
    OK = "OK"


class CaseStartForbiddenCode(str, Enum):
    PERMISSION_DENIED_NOT_IN_ROOM = "PERMISSION_DENIED_NOT_IN_ROOM"
    PERMISSION_DENIED_NOT_HOST = "PERMISSION_DENIED_NOT_HOST"


class CaseStartConflictCode(str, Enum):
    ROOM_CASE_RUNNING = "ROOM_CASE_RUNNING"
    ROOM_NOT_ENOUGH_PLAYERS = "ROOM_NOT_ENOUGH_PLAYERS"
    ROOM_NOT_ALL_READY = "ROOM_NOT_ALL_READY"
    ROOM_DELETED = "ROOM_DELETED"


CaseStartSuccessResponse = Envelope[CaseStartMutation, CaseStartSuccessCode]
CaseStartForbiddenResponse = Envelope[None, CaseStartForbiddenCode]
CaseStartConflictResponse = Envelope[None, CaseStartConflictCode]
