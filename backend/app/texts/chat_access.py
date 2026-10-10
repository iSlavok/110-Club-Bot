from html import escape

from app.schemas import ClubAccess
from app.utils import BUSINESS_TZ


def join_button(club_title: str) -> str:
    return f"Вступить в чат: {club_title}"


def access_line(item: ClubAccess) -> str:
    line = f"Ты в клубе {escape(item.club_title)}, блок {escape(item.block_title)}"
    if item.is_upcoming:
        starts = item.block_starts_at.astimezone(BUSINESS_TZ).strftime("%d.%m")
        return f"{line} — начнётся {starts}."
    return f"{line}."


def invite(item: ClubAccess) -> str:
    return f"{access_line(item)}\nВступай в чат клуба по кнопке ниже — бот одобрит заявку сам."


def kicked(club_title: str) -> str:
    return (
        f"Блок закончился, в списке следующего тебя нет, поэтому бот убрал тебя из чата клуба {escape(club_title)}.\n"
        "Если это ошибка — напиши куратору."
    )
