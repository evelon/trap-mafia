from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class DomainError(Exception):
    """도메인/유스케이스 계층에서 사용하는 베이스 예외.

    - HTTP(FastAPI)와 무관하게 사용한다.
    - repository/service 어디서든 사용할 수 있지만, *HTTP 응답 결정*은 여기서 하지 않는다.
    """


@dataclass(frozen=True, slots=True)
class EntityRef:
    """에러 메시지/로깅에 사용하기 위한 가벼운 엔티티 레퍼런스."""

    entity: str
    identifier: object


class EntityNotFoundError(DomainError):
    """조회 대상 엔티티가 존재하지 않을 때."""

    def __init__(self, entity: str, identifier: object) -> None:
        self.ref = EntityRef(entity=entity, identifier=identifier)
        super().__init__(f"{entity} not found: {identifier}")


class EntityAlreadyExistsError(DomainError):
    """생성/등록 시 이미 존재해서 실패할 때(주로 unique 제약)."""

    def __init__(self, entity: str, identifier: object) -> None:
        self.ref = EntityRef(entity=entity, identifier=identifier)
        super().__init__(f"{entity} already exists: {identifier}")


class ConcurrencyError(DomainError):
    """낙관적 락/동시성 충돌 등으로 커밋이 실패할 때."""

    def __init__(self, message: str = "Concurrency conflict") -> None:
        super().__init__(message)


class PermissionDeniedError(DomainError):
    """권한/정책 위반(예: host만 가능)."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)


class InvalidStateError(DomainError):
    """도메인 상태가 현재 작업을 허용하지 않을 때(상태 전이/룰 위반)."""

    def __init__(self, message: str = "Invalid state") -> None:
        super().__init__(message)


class InvariantViolationError(DomainError):
    """개발자 실수/버그에 가까운 도메인 불변식 위반."""

    def __init__(
        self, message: str = "Invariant violation", *, meta: dict[str, Any] | None = None
    ) -> None:
        self.meta = meta
        super().__init__(message)
