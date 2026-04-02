from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.common.envelope import Envelope
from app.schemas.common.ids import CaseId, RoomId, UserId


class LoginCode(str, Enum):
    OK = "OK"


class GuestInfo(BaseModel):
    id: UserId = Field(description="User ID (UUID)")
    username: str = Field(description="Username")
    current_room_id: RoomId | None = Field(default=None)
    current_case_id: CaseId | None = Field(default=None)


_GuestInfoResponse = Envelope[GuestInfo, LoginCode]
UserInfoResponse = _GuestInfoResponse


class LogoutCode(str, Enum):
    OK = "OK"


_GuestLogoutResponse = Envelope[None, LogoutCode]
LogoutResponse = _GuestLogoutResponse
