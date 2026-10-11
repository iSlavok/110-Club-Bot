from app.exceptions import (
    AdminAccessDeniedError,
    AppError,
    ExternalServiceError,
    InvalidVkLinkError,
    NotFoundError,
    PermissionDeniedError,
    RemovalRequestDecidedError,
    UserNotRegisteredError,
    VkAccountTakenError,
    VkAlreadyLinkedError,
    VkLinkModeChangedError,
    VkLinkUnavailableError,
    VkProfileNotFoundError,
    VkUnavailableError,
)

_MESSAGES: dict[type[AppError], str] = {
    AdminAccessDeniedError: "У тебя нет доступа к админке.",
    UserNotRegisteredError: "Сначала нажми /start.",
    VkAlreadyLinkedError: "ВК уже привязан. Изменить привязку нельзя — по вопросам пиши куратору.",
    VkAccountTakenError: "Этот ВК уже привязан к другому аккаунту. Если это ошибка — напиши куратору.",
    InvalidVkLinkError: "Не похоже на ссылку на страницу ВК. Пришли ссылку вида vk.com/id123 или vk.com/твой_ник.",
    VkProfileNotFoundError: "Не нашёл такую страницу ВК.",
    VkLinkModeChangedError: "Способ привязки ВК изменился. Нажми /vk, чтобы начать заново.",
    VkLinkUnavailableError: "Привязка ВК временно недоступна. Попробуй позже или напиши куратору.",
    VkUnavailableError: "ВК сейчас не отвечает. Попробуй через пару минут.",
    PermissionDeniedError: "У тебя нет прав на это действие.",
    RemovalRequestDecidedError: "По этому запросу уже принято решение.",
    NotFoundError: "Не нашёл то, что ты ищешь.",
    ExternalServiceError: "Внешний сервис сейчас недоступен. Попробуй позже.",
}

DEFAULT = "Не получилось выполнить действие."


def for_error(exc: AppError) -> str:
    for cls in type(exc).__mro__:
        if (text := _MESSAGES.get(cls)) is not None:
            return text
    return DEFAULT
