from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import Field
from pydantic.generics import GenericModel

DataT = TypeVar("DataT")
CodeEnumT = TypeVar("CodeEnumT", bound=str)
Meta = dict[str, object]


class Envelope(GenericModel, Generic[DataT, CodeEnumT]):
    """
    - Keep this as the only top-level shape for every response.
    - Put real payload into `data`.
    """

    ok: bool = Field(description="Domain-level success/failure.")
    code: CodeEnumT = Field(description="Domain result code or snapshot trigger code.")
    message: str | None = Field(default=None, description="Human-friendly optional message.")
    data: DataT | None = Field(default=None, description="Actual json payload of responses.")
    meta: Meta | None = Field(default=None, description="Optional metadata.", examples=[None])
