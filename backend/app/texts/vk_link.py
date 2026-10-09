from html import escape

from app.schemas import ClubAccess, VkAlreadyLinked, VkCandidate, VkLinkByOAuth, VkLinkResult
from app.utils import BUSINESS_TZ

ASK_PROFILE_LINK = (
    "Пришли ссылку на свою страницу VK, например <code>vk.com/id123</code> или <code>vk.com/твой_ник</code>.\n"
    "Привязку потом нельзя изменить, поэтому проверь, что страница твоя."
)
OAUTH_BUTTON = "Войти через VK"
CANCEL_BUTTON = "Отмена"
UNAVAILABLE = "Привязка VK временно недоступна. Попробуй позже или напиши куратору."
CANCELLED = "Хорошо, пришли ссылку на свою страницу VK."
STALE_CONFIRMATION = "Эта кнопка устарела. Нажми /vk, чтобы начать заново."
LINKED = "Готово, VK привязан."
CALLBACK_EXPIRED_TITLE = "Ссылка устарела"
CALLBACK_EXPIRED_TEXT = "Вернись в Telegram и запроси новую ссылку командой /vk в боте клуба."
CALLBACK_DONE_TITLE = "Готово"
CALLBACK_DONE_TEXT = "Вернись в Telegram: бот клуба написал тебе результат."

OAUTH_CANCELLED = "Вход через VK отменён. Нажми /vk, чтобы попробовать ещё раз."
OAUTH_ALREADY_LINKED = "VK уже привязан. Изменить привязку нельзя — по вопросам пиши куратору."
OAUTH_VK_TAKEN = "Этот VK уже привязан к другому Telegram. Напиши куратору."
OAUTH_FAILED = "Не получилось подтвердить вход через VK. Нажми /vk и попробуй ещё раз."


def oauth_offer(offer: VkLinkByOAuth) -> str:
    expires_at = offer.expires_at.astimezone(BUSINESS_TZ).strftime("%H:%M")
    return (
        "Нажми кнопку ниже и войди в VK — так бот убедится, что страница твоя.\n"
        f"Кнопка действует до {expires_at} по Москве. Привязку потом нельзя изменить."
    )


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
        f"VK уже привязан: vk.com/id{offer.vk_id}. Изменить привязку нельзя — по вопросам пиши куратору.\n\n"
        f"{access_status(offer.access)}"
    )


def access_status(access: list[ClubAccess]) -> str:
    if not access:
        return "В текущем блоке тебя нет в списках. Если это ошибка — напиши куратору."
    return "\n".join(f"Ты в клубе {escape(item.club_title)}, блок {escape(item.block_title)}." for item in access)
