from app.exceptions import AppError, ExternalServiceError, NotFoundError

_MESSAGES: dict[type[AppError], str] = {
    NotFoundError: "Не нашёл то, что ты ищешь.",
    ExternalServiceError: "Внешний сервис сейчас недоступен. Попробуй позже.",
}

DEFAULT = "Не получилось выполнить действие."


def for_error(exc: AppError) -> str:
    for cls in type(exc).__mro__:
        if (text := _MESSAGES.get(cls)) is not None:
            return text
    return DEFAULT
