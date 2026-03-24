from enum import Enum
from typing import Annotated

from pydantic import BaseModel


class Target(str, Enum):
    ROOM = "ROOM"
    CASE = "CASE"


class Subject(str, Enum):
    ME = "ME"
    USER = "USER"
    CASE = "CASE"


class BaseMutation[ReasonT: Enum, SubjectIdT](BaseModel):
    """
    공통 Mutation 응답 모델.

    모든 Mutation은 다음 의미를 가진다:
    - target: 변경이 발생한 상위 리소스 (ROOM / CASE 등)
    - subject: 행위의 주체 (ME / USER 등)
    - subject_id: subject가 USER인 경우 대상 식별자, ME인 경우 None
    - on_target: 요청 직후 subject가 target에 속해 있는지 여부
    - changed: 요청으로 인해 실제 상태 변화가 발생했는지 여부
    - reason: 해당 mutation의 세부 결과(enum)

    HTTP status는 transport 수준의 성공/실패만 표현하며,
    도메인 수준의 결과는 changed 및 reason으로 표현한다.
    """

    target: Annotated[Target, "변경이 발생한 상위 리소스 종류"]
    subject: Annotated[Subject, "행위의 주체 종류"]
    subject_id: Annotated[SubjectIdT, "subject에 대응하는 식별자. ME면 None 가능"]
    on_target: Annotated[bool, "요청 직후 subject가 target에 속해 있는지 여부"]
    changed: Annotated[bool, "요청으로 실제 상태 변화가 발생했는지 여부"]
    reason: Annotated[ReasonT, "해당 mutation의 세부 결과 코드"]
