from datetime import datetime
from html import escape

from app.schemas import StudentClubStatus, StudentStatus
from app.utils import BUSINESS_TZ

NOT_LINKED = "VK не привязан. Привяжи его командой /vk: по странице VK бот находит тебя в списках клуба."
NO_ACCESS = "В текущем блоке тебя нет в списках. Если это ошибка — напиши куратору."


def student_status(status: StudentStatus) -> str:
    if status.vk_id is None:
        return NOT_LINKED
    parts = [f"VK: vk.com/id{status.vk_id}"]
    if not status.clubs:
        parts.append(NO_ACCESS)
    parts.extend(_club(club) for club in status.clubs)
    return "\n\n".join(parts)


def _club(status: StudentClubStatus) -> str:
    access = status.access
    block = f"Блок: {escape(access.block_title)} ({_day(access.block_starts_at)}–{_day(access.block_ends_at)})"
    if access.is_upcoming:
        block = f"{block}, ещё не начался"
    lines = [f"<b>{escape(access.club_title)}</b>", block]
    if status.next_block_title is not None:
        lines.append(f"В следующем блоке ({escape(status.next_block_title)}) ты тоже есть.")
    chat = _chat(status)
    if chat is not None:
        lines.append(chat)
    return "\n".join(lines)


def _chat(status: StudentClubStatus) -> str | None:
    if status.in_chat is None:
        return None
    if status.in_chat:
        return "Чат: ты в чате."
    if status.access.invite_link is not None:
        return "Чат: ты ещё не в чате — вступай по кнопке ниже, бот одобрит заявку сам."
    return "Чат: ты ещё не в чате, а ссылку бот сейчас получить не смог. Напиши куратору."


def _day(moment: datetime) -> str:
    return f"{moment.astimezone(BUSINESS_TZ):%d.%m}"
