from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from pydantic import Field

UserId = Annotated[
    UUID,
    Field(description="User identifier (UUID)", examples=["550e8400-e29b-41d4-a716-446655440000"]),
]
RoomId = Annotated[
    UUID,
    Field(description="Room identifier (UUID)", examples=["550e8400-e29b-41d4-a716-446655440000"]),
]
CaseId = Annotated[
    UUID,
    Field(description="Case identifier (UUID)", examples=["550e8400-e29b-41d4-a716-446655440000"]),
]
PhaseId = Annotated[
    UUID,
    Field(description="Phase identifier (UUID)", examples=["550e8400-e29b-41d4-a716-446655440000"]),
]
ConnId = str
# CaseHistoryId = Annotated[int, Field(description="Action identifier", examples=[42])]
# CaseActionHistoryId = Annotated[int, Field(description="Action identifier", examples=[42])]


@dataclass(frozen=True, slots=True)
class UserId_:
    """차후 사용할 UserId Wrapper"""

    value: UUID

    def __init__(self, raw_value: UUID | str):
        v = UUID(raw_value) if isinstance(raw_value, str) else raw_value
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return str(self.value)

    def __hash__(self) -> int:
        return hash(self.value)
