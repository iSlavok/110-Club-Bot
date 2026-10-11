from html import escape

from app.schemas import StudentClubStatus, StudentStatus

NOT_LINKED = "ВК не привязан. Привяжи его командой /vk, чтобы попасть в чат клуба."
NO_ACCESS = "В текущем блоке тебя нет в списках. Если это ошибка — напиши куратору."


def student_status(status: StudentStatus) -> str:
    if status.vk_id is None:
        return NOT_LINKED
    parts = [f"ВК: vk.com/id{status.vk_id}"]
    if not status.clubs:
        parts.append(NO_ACCESS)
    parts.extend(_club(club) for club in status.clubs)
    return "\n\n".join(parts)


def _club(status: StudentClubStatus) -> str:
    access = status.access
    lines = [f"<b>Клуб {escape(access.club_title)}, блок {escape(access.block_title)}</b>"]
    if status.next_block_title is not None:
        lines.append(f"В следующем блоке {escape(status.next_block_title)} ты тоже есть.")
    chat = _chat(status)
    if chat is not None:
        lines.append(chat)
    return "\n".join(lines)


def _chat(status: StudentClubStatus) -> str | None:
    if status.in_chat is None:
        return None
    if status.in_chat:
        return "Ты в чате клуба."
    if status.access.invite_link is not None:
        return "Вступи в чат по кнопке ниже."
    return "Ссылку на чат сейчас получить не удалось. Напиши куратору."
