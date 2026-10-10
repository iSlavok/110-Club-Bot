from dataclasses import dataclass

from app.enums import ChatAccessStatus


@dataclass(frozen=True, slots=True)
class BlockMemberRow:
    vk_id: int
    user_id: int | None
    full_name: str | None
    tg_username: str | None
    chat_status: ChatAccessStatus | None
