from html import escape

from app.schemas import ClubAccess, VkAlreadyLinked, VkCandidate, VkLinkResult

ASK_PROFILE_LINK = (
    "Пришли ссылку на свою страницу VK, например <code>vk.com/id123</code> или <code>vk.com/твой_ник</code>.\n"
    "Привязку потом нельзя изменить, поэтому проверь, что страница твоя."
)
OAUTH_OFFER = (
    "Нажми кнопку ниже и войди в VK — так бот убедится, что страница твоя.\n"
    "Ссылка действует 10 минут. Привязку потом нельзя изменить."
)
OAUTH_BUTTON = "Войти через VK"
CANCEL_BUTTON = "Отмена"
UNAVAILABLE = "Привязка VK временно недоступна. Попробуй позже или напиши куратору."
CANCELLED = "Хорошо, пришли ссылку на свою страницу VK."
STALE_CONFIRMATION = "Эта кнопка устарела. Нажми /vk, чтобы начать заново."
LINKED = "Готово, VK привязан."


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
