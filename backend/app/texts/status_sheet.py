from datetime import datetime

from app.utils import BUSINESS_TZ


def title(block_title: str | None, updated_at: datetime) -> str:
    updated = updated_at.astimezone(BUSINESS_TZ).strftime("%d.%m.%Y %H:%M")
    block = f"Блок «{block_title}»" if block_title is not None else "Сейчас нет блока с доступом"
    return f"{block} · обновлено {updated}"


def no_bot(count: int) -> str:
    return f"Не подключили бота ({count})"


def in_chat(count: int) -> str:
    return f"Зашли в чат ({count})"


def not_joined(count: int) -> str:
    return f"Подключили бота, но не зашли в чат ({count})"


def bot_blocked(count: int) -> str:
    return f"Заблокировали бота, не зашли в чат ({count})"
