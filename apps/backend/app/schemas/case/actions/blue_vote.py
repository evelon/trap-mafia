from enum import Enum

from pydantic import BaseModel, Field


class BlueVoteChoice(str, Enum):
    YES = "YES"
    NO = "NO"
    SKIP = "SKIP"


class BlueVoteRequest(BaseModel):
    """
    POST /api/cases/current/blue-vote 요청 바디.

    의미:
    - VOTE phase에서 현재 target에 대해 YES / NO / SKIP 중 하나를 선택한다.
    """

    choice: BlueVoteChoice = Field(
        description="Vote choice in VOTE phase.",
        examples=["YES", "NO", "SKIP"],
    )
