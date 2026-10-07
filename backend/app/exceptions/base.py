import re
from typing import ClassVar

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def _code_from_class_name(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name.removesuffix("Error")).upper()


class AppError(Exception):
    code: ClassVar[str] = "APP"

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if "code" not in cls.__dict__:
            cls.code = _code_from_class_name(cls.__name__)

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    pass


class InvalidInputError(AppError):
    pass


class ConflictError(AppError):
    pass


class AuthenticationError(AppError):
    pass


class AuthorizationError(AppError):
    pass


class ExternalServiceError(AppError):
    pass


class TooManyRequestsError(AppError):
    pass
