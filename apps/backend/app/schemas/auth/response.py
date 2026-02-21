from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.schemas.common.envelope import Envelope
from app.schemas.common.ids import CaseId, UserId


class LoginCode(str, Enum):
    OK = "OK"


class GuestInfo(BaseModel):
    id: UserId = Field(description="User ID (UUID)")
    username: str = Field(description="Username")
    in_case: bool = Field(description="Whether the user is currently in a case")
    current_case_id: CaseId | None = Field(
        default=None,
        description="Current case id if in_case is true",
    )

    model_config = {
        "json_schema_extra": {
            "description": (
                "If in_case is true, current_case_id must be provided; otherwise it must be null."
            ),
            "if": {
                "properties": {"in_case": {"const": True}},
                "required": ["in_case"],
            },
            "then": {
                "required": ["current_case_id"],
                "properties": {"current_case_id": {"type": "string", "format": "uuid"}},
            },
            "else": {
                "properties": {"current_case_id": {"type": "null"}},
            },
        }
    }

    @model_validator(mode="after")
    def _validate_case_id(self):
        if self.in_case and self.current_case_id is None:
            raise ValueError("current_case_id must be provided when in_case is true")
        if (not self.in_case) and self.current_case_id is not None:
            raise ValueError("current_case_id must be null when in_case is false")
        return self


GuestInfoResponse = Envelope[GuestInfo, LoginCode]


class LogoutCode(str, Enum):
    OK = "OK"


GuestLogoutResponse = Envelope[None, LogoutCode]
