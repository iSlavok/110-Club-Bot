from html import escape

from app.schemas import IssuedLoginCode
from app.utils import BUSINESS_TZ

ADMIN_PANEL_URL_MISSING = "Адрес админки не настроен."


def admin_panel_link(url: str | None) -> str:
    if url is None:
        return ADMIN_PANEL_URL_MISSING
    return f"Админка: {escape(url)}\nВход — кодом из /login."


def login_code(issued: IssuedLoginCode) -> str:
    expires_at = issued.expires_at.astimezone(BUSINESS_TZ).strftime("%H:%M")
    return (
        f"Код для входа в админку: <code>{issued.code}</code>\n"
        f"Действует до {expires_at} по Москве. Никому его не сообщай."
    )
