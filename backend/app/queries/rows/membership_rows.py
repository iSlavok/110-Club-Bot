from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockMemberRow:
    vk_id: int
    user_id: int | None
    full_name: str | None
    tg_username: str | None
