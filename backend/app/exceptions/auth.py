from app.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    InvalidInputError,
    NotFoundError,
    TooManyRequestsError,
)


class NotAuthenticatedError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Not authenticated")


class PermissionDeniedError(AuthorizationError):
    def __init__(self) -> None:
        super().__init__("Not enough permissions")


class AdminAccessDeniedError(AuthorizationError):
    def __init__(self) -> None:
        super().__init__("This Telegram account has no access to the admin panel")


class InvalidLoginCodeError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__("Login code is wrong or expired")


class TooManyLoginAttemptsError(TooManyRequestsError):
    def __init__(self) -> None:
        super().__init__("Too many failed login attempts, try again later")


class InvalidWidgetDataError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__("Telegram login data is invalid or outdated")


class LoginUnavailableError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("Login is temporarily unavailable, try again later")


class TelegramUnavailableError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("Telegram is not reachable right now")


class WidgetLoginDisabledError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Telegram widget login is disabled")
