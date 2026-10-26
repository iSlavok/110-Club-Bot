from enum import StrEnum


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class BlockMemberSort(StrEnum):
    VK = "vk"
    BOT = "bot"
    CHAT = "chat"
