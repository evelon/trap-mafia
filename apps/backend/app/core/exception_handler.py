import logging
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status as http_status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import (
    AuthCommonErrorCode,
    BadRequestErrorCode,
    BaseErrorCode,
    CommonErrorCode,
    ConflictErrorCode,
    NotFoundErrorCode,
)
from app.core.exceptions import EnvelopeHTTPException
from app.domain.case_logic.night import NightRuleViolationError, NightRuleViolationReason
from app.domain.exceptions.common import (
    ConcurrencyError,
    DomainError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InvalidStateError,
    PermissionDeniedError,
    RoomCaseAlreadyRunningError,
)
from app.schemas.common.envelope import Envelope

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ErrorEnvelopeSpec:
    status_code: int
    code: BaseErrorCode
    message: str | None = None
    data: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


def _common_code_for_http_exception(status_code: int) -> BaseErrorCode:
    """Map HTTP status to a CommonErrorCode.

    This keeps auth/permission errors (401/403) in the Envelope format.
    The enum member names below are *optional*; if your CommonErrorCode
    doesn't define them yet, we fall back to UNKNOWN_ERROR.
    """

    # Prefer explicit codes if your enum defines them.
    if status_code == http_status.HTTP_401_UNAUTHORIZED:
        return AuthCommonErrorCode.AUTH_UNAUTHORIZED

    if status_code == http_status.HTTP_403_FORBIDDEN:
        return CommonErrorCode.PERMISSION_DENIED

    if status_code == http_status.HTTP_404_NOT_FOUND:
        return CommonErrorCode.NOT_FOUND

    return CommonErrorCode.UNKNOWN_ERROR


def _common_code_for_domain_error(exc: DomainError) -> BaseErrorCode:
    """Map domain-level errors to a CommonErrorCode.

    This keeps repository/service-raised domain errors in the Envelope format.
    If the target enum member doesn't exist, we fall back to UNKNOWN_ERROR.
    """

    def _maybe(member_name: str) -> BaseErrorCode | None:
        return getattr(CommonErrorCode, member_name, None)  # type: ignore[return-value]

    if isinstance(exc, EntityNotFoundError):
        return _maybe("NOT_FOUND") or CommonErrorCode.UNKNOWN_ERROR

    if isinstance(exc, EntityAlreadyExistsError):
        return _maybe("CONFLICT") or _maybe("ALREADY_EXISTS") or CommonErrorCode.UNKNOWN_ERROR

    if isinstance(exc, PermissionDeniedError):
        return _maybe("PERMISSION_DENIED") or CommonErrorCode.UNKNOWN_ERROR

    if isinstance(exc, (InvalidStateError, ConcurrencyError)):
        return _maybe("CONFLICT") or CommonErrorCode.UNKNOWN_ERROR

    return CommonErrorCode.UNKNOWN_ERROR


def _spec_for_domain_error(exc: DomainError) -> ErrorEnvelopeSpec:
    if isinstance(exc, NightRuleViolationError):
        if exc.reason == NightRuleViolationReason.INVALID_TARGET_SEAT:
            return ErrorEnvelopeSpec(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                code=BadRequestErrorCode.BAD_REQUEST_INVALID_TARGET_SEAT,
                message=str(exc) or None,
            )

        if exc.reason == NightRuleViolationReason.SELF_VOTE:
            return ErrorEnvelopeSpec(
                status_code=http_status.HTTP_409_CONFLICT,
                code=ConflictErrorCode.CONFLICT_NIGHT_REJECTED_SELF_VOTE,
                message=str(exc) or None,
            )

        if exc.reason == NightRuleViolationReason.ALREADY_ACTED:
            return ErrorEnvelopeSpec(
                status_code=http_status.HTTP_409_CONFLICT,
                code=ConflictErrorCode.CONFLICT_PHASE_REJECTED_ALREADY_DECIDED,
                message=str(exc) or None,
            )

        if exc.reason == NightRuleViolationReason.NOT_ALIVE:
            return ErrorEnvelopeSpec(
                status_code=http_status.HTTP_409_CONFLICT,
                code=ConflictErrorCode.CONFLICT_PLAYER_NOT_ALIVE,
                message=str(exc) or None,
            )

        return ErrorEnvelopeSpec(
            status_code=http_status.HTTP_409_CONFLICT,
            code=ConflictErrorCode.CONFLICT_PHASE_REJECTED_CONFLICT_ACTION,
            message=str(exc) or None,
        )

    if isinstance(exc, EntityNotFoundError):
        entity_specs: dict[str, ErrorEnvelopeSpec] = {
            "Room": ErrorEnvelopeSpec(
                status_code=http_status.HTTP_404_NOT_FOUND,
                code=NotFoundErrorCode.NOT_FOUND_ROOM,
                message=str(exc),
                data={"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)},
            ),
            "CurrentPhase": ErrorEnvelopeSpec(
                status_code=http_status.HTTP_409_CONFLICT,
                code=ConflictErrorCode.CONFLICT_PHASE_NOT_FOUND,
                message=str(exc),
                data={"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)},
            ),
            "Case": ErrorEnvelopeSpec(
                status_code=http_status.HTTP_409_CONFLICT,
                code=ConflictErrorCode.CONFLICT_CASE_NOT_FOUND,
                message=str(exc),
                data={"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)},
            ),
            "Actor": ErrorEnvelopeSpec(
                status_code=http_status.HTTP_409_CONFLICT,
                code=ConflictErrorCode.CONFLICT_ACTOR_NOT_FOUND,
                message=str(exc),
                data={"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)},
            ),
        }
        return entity_specs.get(
            exc.ref.entity,
            ErrorEnvelopeSpec(
                status_code=http_status.HTTP_404_NOT_FOUND,
                code=_common_code_for_domain_error(exc),
                message=str(exc),
                data={"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)},
            ),
        )

    if isinstance(exc, EntityAlreadyExistsError):
        return ErrorEnvelopeSpec(
            status_code=http_status.HTTP_409_CONFLICT,
            code=_common_code_for_domain_error(exc),
            message=str(exc),
            data={"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)},
        )

    if isinstance(exc, RoomCaseAlreadyRunningError):
        return ErrorEnvelopeSpec(
            status_code=http_status.HTTP_409_CONFLICT,
            code=ConflictErrorCode.CONFLICT_ROOM_CASE_RUNNING,
            message=str(exc),
        )

    if isinstance(exc, PermissionDeniedError):
        return ErrorEnvelopeSpec(
            status_code=http_status.HTTP_403_FORBIDDEN,
            code=_common_code_for_domain_error(exc),
            message=str(exc) or None,
        )

    if isinstance(exc, (InvalidStateError, ConcurrencyError)):
        return ErrorEnvelopeSpec(
            status_code=http_status.HTTP_409_CONFLICT,
            code=_common_code_for_domain_error(exc),
            message=str(exc) or None,
            meta=getattr(exc, "meta", None),
        )

    return ErrorEnvelopeSpec(
        status_code=http_status.HTTP_400_BAD_REQUEST,
        code=_common_code_for_domain_error(exc),
        message=str(exc) or None,
        meta=getattr(exc, "meta", None),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        fields = []

        for err in exc.errors():
            loc = ".".join(str(x) for x in err["loc"])
            fields.append(
                {
                    "field": loc,
                    "message": err["msg"],
                    "type": err["type"],
                }
            )

        return JSONResponse(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=Envelope[dict, CommonErrorCode](
                ok=False,
                code=CommonErrorCode.VALIDATION_ERROR,
                message=None,
                data={"fields": fields},
                meta=None,
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # If some code path already raised an EnvelopeException, return its envelope response.
        if isinstance(exc, EnvelopeHTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_envelope_dict(),
            )

        return JSONResponse(
            status_code=exc.status_code,
            content=Envelope[dict, BaseErrorCode](
                ok=False,
                code=_common_code_for_http_exception(exc.status_code),
                message=str(exc.detail) if exc.detail is not None else None,
                data=None,
                meta=None,
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Starlette can raise its own HTTPException (e.g., for routing/404).
        return JSONResponse(
            status_code=exc.status_code,
            content=Envelope[dict, BaseErrorCode](
                ok=False,
                code=_common_code_for_http_exception(exc.status_code),
                message=str(exc.detail) if exc.detail is not None else None,
                data=None,
                meta=None,
            ).model_dump(),
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        spec = _spec_for_domain_error(exc)

        return JSONResponse(
            status_code=spec.status_code,
            content=Envelope[dict, BaseErrorCode](
                ok=False,
                code=spec.code,
                message=spec.message,
                data=spec.data,
                meta=spec.meta,
            ).model_dump(),
        )

    @app.exception_handler(EnvelopeHTTPException)
    async def envelope_http_exception_handler(request: Request, exc: EnvelopeHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_envelope_dict(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # NOTE: 예상하지 못한 서버 내부 오류는 500 + Envelope로 통일한다.
        # 내부 예외 상세는 응답으로 노출하지 않고, 로그로만 남긴다.
        logger.exception("Unhandled exception", exc_info=exc)

        return JSONResponse(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=Envelope[dict, BaseErrorCode](
                ok=False,
                code=CommonErrorCode.INTERNAL_SERVER_ERROR,
                message=None,
                data=None,
                meta=None,
            ).model_dump(),
        )
