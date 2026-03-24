from enum import Enum

from app.schemas.common.envelope import Envelope
from app.schemas.room.mutation import (
    CaseStartMutation,
    JoinRoomMutation,
    KickUserMutation,
    LeaveRoomMutation,
)


class JoinRoomCode(str, Enum):
    OK = "OK"


class JoinRoomResponse(Envelope[JoinRoomMutation, JoinRoomCode]):
    @classmethod
    def default_ok_code(cls) -> JoinRoomCode:
        return JoinRoomCode.OK


class LeaveRoomCode(str, Enum):
    OK = "OK"


class LeaveRoomResponse(Envelope[LeaveRoomMutation, LeaveRoomCode]):
    @classmethod
    def default_ok_code(cls) -> LeaveRoomCode:
        return LeaveRoomCode.OK


class KickUserCode(str, Enum):
    OK = "OK"


class KickUserResponse(Envelope[KickUserMutation, KickUserCode]):
    @classmethod
    def default_ok_code(cls) -> KickUserCode:
        return KickUserCode.OK


class CaseStartSuccessCode(str, Enum):
    OK = "OK"


class CaseStartResponse(Envelope[CaseStartMutation, CaseStartSuccessCode]):
    @classmethod
    def default_ok_code(cls) -> CaseStartSuccessCode:
        return CaseStartSuccessCode.OK


class CaseStartForbiddenCode(str, Enum):
    PERMISSION_DENIED_NOT_IN_ROOM = "PERMISSION_DENIED_NOT_IN_ROOM"
    PERMISSION_DENIED_NOT_HOST = "PERMISSION_DENIED_NOT_HOST"


CaseStartForbiddenResponse = Envelope[None, CaseStartForbiddenCode]


class CaseStartConflictCode(str, Enum):
    ROOM_CASE_RUNNING = "ROOM_CASE_RUNNING"
    ROOM_NOT_ENOUGH_PLAYERS = "ROOM_NOT_ENOUGH_PLAYERS"
    ROOM_NOT_ALL_READY = "ROOM_NOT_ALL_READY"
    ROOM_DELETED = "ROOM_DELETED"


CaseStartConflictResponse = Envelope[None, CaseStartConflictCode]
