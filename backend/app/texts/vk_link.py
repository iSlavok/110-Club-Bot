from html import escape

from app.schemas import ClubAccess, VkAlreadyLinked, VkCandidate, VkLinkResult
from app.texts.chat_access import access_line
from app.texts.student_status import NO_ACCESS

ASK_PROFILE_LINK = (
    "Пришли ссылку на свою страницу ВК, например <code>vk.com/id123</code> или <code>vk.com/твой_ник</code>."
)
OAUTH_BUTTON = "Войти через ВК"
CANCEL_BUTTON = "Отмена"
UNAVAILABLE = "Привязка ВК временно недоступна. Попробуй позже или напиши куратору."
CANCELLED = "Хорошо, пришли ссылку на свою страницу ВК."
STALE_CONFIRMATION = "Эта кнопка устарела. Нажми /vk, чтобы начать заново."
LINKED = "Готово, ВК привязан."
CALLBACK_EXPIRED_TITLE = "Ссылка устарела"
CALLBACK_EXPIRED_TEXT = "Вернись в Telegram и запроси новую ссылку командой /vk в боте клуба."
CALLBACK_DONE_TITLE = "Готово"
CALLBACK_DONE_TEXT = "Вернись в Telegram: бот клуба написал тебе результат."

JOIN_HINT = "Вступи в чат по кнопке ниже."

OAUTH_CANCELLED = "Вход через ВК отменён. Нажми /vk, чтобы попробовать ещё раз."
OAUTH_ALREADY_LINKED = "ВК уже привязан. Изменить привязку нельзя — по вопросам пиши куратору."
OAUTH_VK_TAKEN = "Этот ВК уже привязан к другому аккаунту. Если это ошибка — напиши куратору."
OAUTH_FAILED = "Не получилось подтвердить вход через ВК. Нажми /vk и попробуй ещё раз."
OAUTH_OFFER = "Нажми кнопку ниже и войди в ВК — так бот убедится, что страница твоя. Привязку потом нельзя изменить."


def confirm_button(candidate: VkCandidate) -> str:
    return f"Это я: {candidate.full_name}"


def confirm_candidate(candidate: VkCandidate) -> str:
    return (
        f"Это твоя страница?\n<b>{escape(candidate.full_name)}</b> — vk.com/id{candidate.vk_id}\n\n"
        "После подтверждения привязку нельзя будет изменить."
    )


def linked(result: VkLinkResult) -> str:
    return f"{LINKED}\n\n{access_status(result.access)}"


def already_linked(offer: VkAlreadyLinked) -> str:
    return (
        f"ВК уже привязан: vk.com/id{offer.vk_id}. Изменить привязку нельзя — по вопросам пиши куратору.\n"
        "Клуб, блок и чат — /status."
    )


def access_status(access: list[ClubAccess]) -> str:
    if not access:
        return NO_ACCESS
    lines = [access_line(item) for item in access]
    if any(item.invite_link for item in access):
        lines.append(JOIN_HINT)
    return "\n".join(lines)
