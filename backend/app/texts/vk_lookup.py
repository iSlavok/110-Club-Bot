from html import escape

from app.schemas import UserDTO

NO_TARGET = "Отправь /vk ответом на сообщение ученика."
NO_PERMISSION = "Смотреть VK учеников можно с правом «Просмотр пользователей бота» в админке."


# The link opens the page; the same address in <code> is copied with one tap.
def student_vk(tg_id: int, full_name: str, user: UserDTO | None) -> str:
    mention = f'<a href="tg://user?id={tg_id}">{escape(full_name)}</a>'
    if user is None:
        return f"{mention} ещё не писал боту, его VK неизвестен."
    if user.vk_id is None:
        return f"{mention} не привязал VK."
    url = f"https://vk.com/id{user.vk_id}"
    return f'VK ученика {mention}:\n<a href="{url}">Открыть страницу</a>\nСкопировать ссылку: <code>{url}</code>'
