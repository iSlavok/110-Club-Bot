from datetime import datetime

from app.enums import BlockMemberState, ChatAccessStatus
from app.utils import BUSINESS_TZ

BLOCK_MEMBER_HEADERS = ("VK", "VK ID", "Имя в Telegram", "Telegram", "Бот", "Чат", "Зашёл в чат")
USER_HEADERS = ("Имя в Telegram", "Telegram", "Telegram ID", "VK", "VK привязан", "Первый /start")

BOT_LINKED = "подключил"
BOT_MISSING = "не подключил"

CHAT_STATUS = {
    ChatAccessStatus.INVITED: "приглашён",
    ChatAccessStatus.JOINED: "в чате",
    ChatAccessStatus.LEFT: "вышел",
    ChatAccessStatus.KICKED: "удалён",
}

# ASCII file names: the state goes into Content-Disposition, which needs no escaping then.
BLOCK_MEMBERS_FILE_SUFFIX = {
    None: "all",
    BlockMemberState.IN_CHAT: "in-chat",
    BlockMemberState.NOT_IN_CHAT: "not-in-chat",
    BlockMemberState.NO_BOT: "no-bot",
    BlockMemberState.NOT_JOINED: "not-joined",
}


def vk_url(vk_id: int) -> str:
    return f"https://vk.com/id{vk_id}"


def telegram(username: str | None) -> str | None:
    return None if username is None else f"@{username}"


def moment(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(BUSINESS_TZ).strftime("%d.%m.%Y %H:%M")
