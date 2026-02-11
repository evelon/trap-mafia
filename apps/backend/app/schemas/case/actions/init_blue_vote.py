from pydantic import BaseModel, Field

from app.domain.types import SeatNo


class InitBlueVoteRequest(BaseModel):
    """
    POST /api/cases/current/init-blue-vote 요청 바디.

    의미:
    - DISCUSS phase에서 blue-vote의 대상 seat_no를 지정하여 VOTE phase 시작을 요청한다.

    필드 해석:
    - target_seat_no: 유효한 seat_no(SeatNo)
    """

    target_seat_no: SeatNo = Field(
        description="Target seat no.",
        examples=[0, 3],
    )
