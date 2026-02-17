from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.schemas.common.envelope import Envelope
from app.schemas.common.error import CommonErrorCode


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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=Envelope[None, CommonErrorCode](
                ok=False,
                code=CommonErrorCode.VALIDATION_ERROR,
                message=None,
                data=None,
                meta=None,
            ).model_dump(),
        )
