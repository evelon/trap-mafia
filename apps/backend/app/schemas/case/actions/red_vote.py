from pydantic import BaseModel, Field

from app.domain.types import SeatNo


class RedVoteRequest(BaseModel):
    """
    POST /api/cases/current/red-vote 요청 바디.

    의미:
    - NIGHT phase에서 red-vote 대상 seat_no를 지정한다.
    - skip인 경우 target_seat_no를 null로 전송한다.

    필드 해석:
    - target_seat_no: 유효한 seat_no(SeatNo), 또는 skip(null)
    """

    target_seat_no: SeatNo | None = Field(
        default=None,
        description="Target seat no. null means skip.",
        examples=[0, 3, None],
    )
