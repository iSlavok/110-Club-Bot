from html import escape

from app.schemas import UserDTO

UNEXPECTED_ERROR = "Что-то пошло не так. Попробуй ещё раз чуть позже."


def greeting(user: UserDTO) -> str:
    return (
        f"Привет, {escape(user.full_name)}! Это бот клуба Ш.\n"
        "Через него ты попадёшь в чат клуба. Для этого привяжи свой ВК."
    )
