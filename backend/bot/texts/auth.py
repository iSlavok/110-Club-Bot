from app.schemas import IssuedLoginCode
from app.utils import BUSINESS_TZ


def login_code(issued: IssuedLoginCode) -> str:
    expires_at = issued.expires_at.astimezone(BUSINESS_TZ).strftime("%H:%M")
    return (
        f"Код для входа в админку: <code>{issued.code}</code>\n"
        f"Действует до {expires_at} по Москве. Никому его не сообщай."
    )
