from __future__ import annotations

from typing import Annotated

from pydantic import Field

from app.domain.constants import SEAT_NO_MAX_EXCLUSIVE, SEAT_NO_MIN

"""
도메인 타입 정의 모듈.

의미:
- 게임 로직에서 반복적으로 사용되는 값의 제약을
  타입 레벨에서 강제하기 위한 공통 타입을 정의한다.
- Pydantic validation과 OpenAPI 문서 생성을 동시에 만족시키는 것을 목표로 한다.
"""


SeatNo = Annotated[
    int,
    Field(
        ge=SEAT_NO_MIN,
        lt=SEAT_NO_MAX_EXCLUSIVE,
        description=f"Seat number ({SEAT_NO_MIN} <= seat_no < {SEAT_NO_MAX_EXCLUSIVE}).",
        examples=[0, 3],
    ),
]
"""
SeatNo

의미:
- case 내에서 플레이어를 식별하는 좌석 번호.
- 0 이상, MAX_SEAT_COUNT 미만의 정수만 허용한다.

설계 의도:
- 모든 action request에서 동일한 범위를 보장한다.
- seat 범위 변경 시 constants.py만 수정하면 된다.
"""
