from enum import StrEnum


class RemovalRequestStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RemovalDecision(StrEnum):
    CONFIRM = "confirm"
    REJECT = "reject"
