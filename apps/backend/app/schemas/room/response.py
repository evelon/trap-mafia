from enum import Enum

from app.core.error_codes import ConflictErrorCode, PermissionErrorCode
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


CaseStartForbiddenResponse = Envelope[None, PermissionErrorCode]


CaseStartConflictResponse = Envelope[None, ConflictErrorCode]
