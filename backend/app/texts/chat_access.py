from html import escape

from app.schemas import ClubAccess


def join_button(club_title: str) -> str:
    return f"Вступить в чат клуба {club_title}"


def access_line(item: ClubAccess) -> str:
    return f"Ты в клубе {escape(item.club_title)}, блок {escape(item.block_title)}."


def invite(item: ClubAccess) -> str:
    return f"{access_line(item)}\nВступи в чат по кнопке ниже."


def kicked(club_title: str) -> str:
    return (
        f"Тебя нет в списке текущего блока клуба {escape(club_title)}, поэтому бот убрал тебя из чата.\n"
        "Если это ошибка — напиши куратору."
    )
