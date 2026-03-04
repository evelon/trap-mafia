from __future__ import annotations

from enum import Enum
from typing import Any, Generic, Self, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")
CodeEnumT = TypeVar("CodeEnumT", bound=Enum)
Meta = dict[str, Any]


class Envelope(BaseModel, Generic[DataT, CodeEnumT]):
    """
    - Keep this as the only top-level shape for every response.
    - Put real payload into `data`.
    """

    ok: bool = Field(description="Domain-level success/failure.")
    code: CodeEnumT = Field(description="Domain result code or snapshot trigger code.")
    message: str | None = Field(default=None, description="Human-friendly optional message.")
    data: DataT | None = Field(
        default=None,
        description="Actual json payload of responses.",
    )
    meta: Meta | None = Field(default=None, description="Optional metadata.", examples=[None])

    @classmethod
    def default_ok_code(cls) -> CodeEnumT:
        """서브클래스에서 OK code를 제공해야 한다."""
        raise NotImplementedError("Envelope.default_ok_code() is not implemented")

    @classmethod
    def success(
        cls,
        *,
        code: CodeEnumT | None = None,
        data: DataT | None = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Self:
        if code is None:
            code = cls.default_ok_code()
        return cls(ok=True, code=code, message=message, data=data, meta=meta)

    @classmethod
    def fail(
        cls,
        *,
        code: CodeEnumT,
        message: str | None = None,
        data: DataT | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Self:
        return cls(ok=False, code=code, message=message, data=data, meta=meta)
