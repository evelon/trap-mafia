from __future__ import annotations

from typing import Any

from fastapi import status
from pydantic import BaseModel

from app.schemas.common.envelope import Envelope
from app.schemas.common.error import CommonErrorCode


class ValidationFieldError(BaseModel):
    field: str
    message: str
    type: str


class ValidationErrorMeta(BaseModel):
    fields: list[ValidationFieldError]


ValidationErrorResponse = Envelope[None, CommonErrorCode]

COMMON_422_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ValidationErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "message": None,
                    "data": None,
                    "meta": {"fields": [{"field": "body.xxx", "message": "...", "type": "..."}]},
                }
            }
        },
    }
}
