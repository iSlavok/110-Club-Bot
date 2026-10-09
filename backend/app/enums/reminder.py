from enum import StrEnum


class ReminderKind(StrEnum):
    LESSON_UPCOMING = "lesson_upcoming"
    LESSON_STARTING = "lesson_starting"
    HOMEWORK_DEADLINE = "homework_deadline"
    LESSON_RESCHEDULED = "lesson_rescheduled"
    LESSON_CANCELLED = "lesson_cancelled"
    HOMEWORK_DEADLINE_CHANGED = "homework_deadline_changed"
    HOMEWORK_REMOVED = "homework_removed"


class ReminderStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
