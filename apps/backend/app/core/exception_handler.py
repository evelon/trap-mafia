import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status as http_status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import EnvelopeHTTPException
from app.domain.exceptions import (
    ConcurrencyError,
    DomainError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InvalidStateError,
    PermissionDeniedError,
)
from app.schemas.common.envelope import Envelope
from app.schemas.common.error import AuthErrorCode, BaseErrorCode, CommonErrorCode

logger = logging.getLogger(__name__)


def _common_code_for_http_exception(status_code: int) -> BaseErrorCode:
    """Map HTTP status to a CommonErrorCode.

    This keeps auth/permission errors (401/403) in the Envelope format.
    The enum member names below are *optional*; if your CommonErrorCode
    doesn't define them yet, we fall back to UNKNOWN_ERROR.
    """

    # Prefer explicit codes if your enum defines them.
    if status_code == http_status.HTTP_401_UNAUTHORIZED:
        return AuthErrorCode.AUTH_UNAUTHORIZED

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
        # NOTE: DomainError는 HTTP와 무관한 계층에서 올라온 예외이므로,
        # 여기서 공통적으로 Envelope + HTTP status로 매핑한다.
        status_code = http_status.HTTP_400_BAD_REQUEST
        data = None

        if isinstance(exc, EntityNotFoundError):
            status_code = http_status.HTTP_404_NOT_FOUND
            data = {"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)}

        elif isinstance(exc, EntityAlreadyExistsError):
            status_code = http_status.HTTP_409_CONFLICT
            data = {"entity": exc.ref.entity, "identifier": str(exc.ref.identifier)}

        elif isinstance(exc, PermissionDeniedError):
            status_code = http_status.HTTP_403_FORBIDDEN

        elif isinstance(exc, (InvalidStateError, ConcurrencyError)):
            status_code = http_status.HTTP_409_CONFLICT

        return JSONResponse(
            status_code=status_code,
            content=Envelope[dict, BaseErrorCode](
                ok=False,
                code=_common_code_for_domain_error(exc),
                message=str(exc) if str(exc) else None,
                data=data,
                meta=getattr(exc, "meta", None),
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
