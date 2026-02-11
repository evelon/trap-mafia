from typing import Annotated

from pydantic import Field

UtcDateTime = Annotated[
    str,
    Field(
        description="UTC datetime string (ISO 8601) with millisecond precision, ends with 'Z'.",
        examples=["2026-02-10T07:12:34.567Z"],
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
    ),
]
