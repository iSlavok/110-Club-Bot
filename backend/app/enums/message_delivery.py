from enum import StrEnum


class MessageDelivery(StrEnum):
    SENT = "sent"
    BOT_BLOCKED = "bot_blocked"
    FAILED = "failed"
