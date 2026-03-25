from __future__ import annotations

from typing import Any

from fastapi import status
from pydantic import BaseModel

from app.core.error_codes import AuthTokenErrorCode, CommonErrorCode
from app.schemas.common.envelope import Envelope


class _ValidationFieldError(BaseModel):
    field: str
    message: str
    type: str


class _ValidationErrorData(BaseModel):
    fields: list[_ValidationFieldError]


class ValidationErrorResponse(Envelope[_ValidationErrorData, CommonErrorCode]):
    pass


COMMON_422_VALIDATION_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "Request body is not matched with pydantic request model",
        "model": ValidationErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "validation_error": {
                        "value": {
                            "ok": False,
                            "code": CommonErrorCode.VALIDATION_ERROR.value,
                            "message": "null",
                            "data": {
                                "fields": [{"field": "body.xxx", "message": "...", "type": "..."}]
                            },
                            "meta": "null",
                        }
                    }
                }
            }
        },
    }
}


class TokenAuthErrorResponse(Envelope[None, AuthTokenErrorCode]):
    pass


COMMON_401_TOKEN_AUTH_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "No token, invalid token, invalid payload, etc.",
        "model": TokenAuthErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "token_expired": {
                        "value": {
                            "ok": False,
                            "code": AuthTokenErrorCode.AUTH_TOKEN_EXPIRED.value,
                            "message": "null",
                            "data": "null",
                            "meta": "null",
                        }
                    }
                }
            }
        },
    }
}
