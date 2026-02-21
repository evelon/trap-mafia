from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import HTTPException


class EnvelopeException(HTTPException):
    """Envelope 형태로 응답하고 싶은 커스텀 예외.

    - FastAPI의 `HTTPException`을 상속해서, 라우터/서비스 어디서든 `raise`로 던질 수 있게 한다.
    - 예외 핸들러에서 `exc.to_envelope_dict()`를 사용해 일관된 Envelope 응답을 만든다.

    Notes
    -----
    - `code`는 프로젝트에서 사용하는 Enum(예: AuthErrorCode, RoomErrorCode 등)을 그대로 받는다.
    - `message`, `data`, `meta`는 필요할 때만 채우면 된다.
    """

    def __init__(
        self,
        *,
        status_code: int,
        response_code: Enum,
        message: str | None = None,
        data: Any = None,
        meta: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        # HTTPException의 detail은 우리가 따로 Envelope로 감싸서 내려줄 거라,
        # 여기서는 디버깅용으로만 가볍게 넣는다(핸들러에서 사용하지 않아도 됨).
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = response_code
        self.message = message
        self.data = data
        self.meta = meta

    def to_envelope_dict(self) -> dict[str, Any]:
        """Envelope JSON payload(dict)로 변환한다.

        Exception handler에서 그대로 JSONResponse(content=...)에 넣을 수 있는 형태.
        """

        return {
            "ok": False,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "meta": self.meta,
        }


def raise_envelope(
    *,
    status_code: int,
    code: Enum,
    message: str | None = None,
    data: Any = None,
    meta: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> None:
    """호출부에서 더 짧게 쓰고 싶을 때 쓰는 헬퍼.

    Usage
    -----
    - `raise_envelope(status_code=401, code=AuthErrorCode.UNAUTHORIZED, message="...")`
    """

    raise EnvelopeException(
        status_code=status_code,
        response_code=code,
        message=message,
        data=data,
        meta=meta,
        headers=headers,
    )
