from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel


class Target(str, Enum):
    ROOM = "ROOM"
    CASE = "CASE"


class Subject(str, Enum):
    ME = "ME"
    USER = "USER"


ReasonT = TypeVar("ReasonT", bound=Enum)
SubjectIdT = TypeVar("SubjectIdT")


class BaseMutation(BaseModel, Generic[ReasonT, SubjectIdT]):
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

    target: Target
    subject: Subject
    subject_id: SubjectIdT
    on_target: bool
    changed: bool
    reason: ReasonT
