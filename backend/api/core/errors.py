from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

from app.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    InvalidInputError,
    NotFoundError,
)

_STATUS_BY_TAG: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidInputError: status.HTTP_400_BAD_REQUEST,
    ConflictError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
}


class ErrorResponse(BaseModel):
    code: str = Field(description="Machine-readable error code, e.g. LESSON_NOT_FOUND")
    message: str = Field(description="Human-readable description")


def _status_for(exc: AppError) -> int:
    for cls in type(exc).__mro__:
        if (code := _STATUS_BY_TAG.get(cls)) is not None:
            return code
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorResponse(code=code, message=message).model_dump())


async def _app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    app_error = cast("AppError", exc)
    return _error(_status_for(app_error), app_error.code, app_error.message)


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    validation_error = cast("RequestValidationError", exc)
    return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, "VALIDATION_FAILED", str(validation_error.errors()))


async def _unhandled_error_handler(request: Request, _: Exception) -> JSONResponse:
    logger.exception("Unhandled error on {} {}", request.method, request.url.path)
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "Internal server error")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
