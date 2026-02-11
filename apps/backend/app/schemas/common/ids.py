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
# CaseHistoryId = Annotated[int, Field(description="Action identifier", examples=[42])]
# CaseActionHistoryId = Annotated[int, Field(description="Action identifier", examples=[42])]
