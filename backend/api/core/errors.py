from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from api.schemas import ErrorResponse, FieldError, ValidationErrorResponse
from app.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    InvalidInputError,
    NotFoundError,
    TooManyRequestsError,
)

_STATUS_BY_TAG: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidInputError: status.HTTP_400_BAD_REQUEST,
    ConflictError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    TooManyRequestsError: status.HTTP_429_TOO_MANY_REQUESTS,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
}

ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    "4XX": {"model": ErrorResponse, "description": "Domain or auth error"},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse, "description": "Invalid request"},
}


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
    errors = cast("RequestValidationError", exc).errors()
    body = ValidationErrorResponse(
        code="VALIDATION_FAILED",
        message="Request validation failed",
        fields=[FieldError(loc=list(error["loc"]), message=error["msg"]) for error in errors],
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=body.model_dump())


async def _unhandled_error_handler(request: Request, _: Exception) -> JSONResponse:
    logger.exception("Unhandled error on {} {}", request.method, request.url.path)
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "Internal server error")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
