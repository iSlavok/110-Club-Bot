from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import LessonKind, ReminderKind, ReminderStatus, ReminderView
from app.schemas import LessonDTO, PageParams, ReminderWithLessonDTO
from app.types import PositiveBigInt


class ReminderListParams(PageParams):
    view: ReminderView = Field(
        default=ReminderView.PENDING,
        description="pending: soonest first; sent: latest sent first; all: every status, latest first",
    )
    include_cancelled: bool = Field(
        default=False,
        description="Also show cancelled reminders; in the pending view only those that would still be ahead",
    )
    lesson_id: PositiveBigInt | None = Field(default=None, description="Only the reminders of this lesson")


class ReminderLessonResponse(BaseModel):
    id: int = Field(description="Lesson id")
    kind: LessonKind = Field(description="Teacher's lesson or a call with the curator")
    title: str = Field(description="Lesson topic")
    starts_at: datetime = Field(description="Start time, UTC")
    is_cancelled: bool = Field(description="Whether the lesson is cancelled")

    @classmethod
    def from_dto(cls, lesson: LessonDTO) -> Self:
        return cls(
            id=lesson.id,
            kind=lesson.kind,
            title=lesson.title,
            starts_at=lesson.starts_at,
            is_cancelled=lesson.is_cancelled,
        )


class ReminderResponse(BaseModel):
    id: int = Field(description="Reminder id")
    lesson: ReminderLessonResponse = Field(description="Lesson the reminder is about")
    kind: ReminderKind = Field(description="What the message says")
    send_at: datetime = Field(description="When it goes or went out, UTC")
    status: ReminderStatus = Field(description="Delivery status")
    attempts: int = Field(description="Send attempts made")
    sent_at: datetime | None = Field(description="When it was sent, UTC")
    error: str | None = Field(description="Last error or the reason it was skipped")

    @classmethod
    def from_dto(cls, reminder: ReminderWithLessonDTO) -> Self:
        return cls(
            id=reminder.id,
            lesson=ReminderLessonResponse.from_dto(reminder.lesson),
            kind=reminder.kind,
            send_at=reminder.send_at,
            status=reminder.status,
            attempts=reminder.attempts,
            sent_at=reminder.sent_at,
            error=reminder.error,
        )


class ReminderPreviewResponse(BaseModel):
    html: str = Field(description="Message text in Telegram HTML, admin-entered parts escaped")
