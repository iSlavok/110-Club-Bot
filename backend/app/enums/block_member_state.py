from enum import StrEnum


class BlockMemberState(StrEnum):
    IN_CHAT = "in_chat"
    NOT_IN_CHAT = "not_in_chat"
    NO_BOT = "no_bot"
    NOT_JOINED = "not_joined"
