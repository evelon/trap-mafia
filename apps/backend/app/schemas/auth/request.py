from typing import Annotated

from pydantic import Field

from app.schemas.base import RequiredFieldsModel

# Type alias for username
Username = Annotated[
    str,
    Field(
        min_length=3,
        max_length=32,
        description="Guest username (3..32)",
        examples=["jolim"],
    ),
]


class GuestLoginRequest(RequiredFieldsModel):
    username: Username
