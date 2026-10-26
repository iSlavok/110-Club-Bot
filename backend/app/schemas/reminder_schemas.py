from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import ReminderKind, ReminderStatus
from app.models import Reminder
from app.schemas.club_schemas import Moment
from app.schemas.lesson_schemas import LessonDraft, LessonDTO


class ReminderDTO(BaseModel):
    id: int
    club_id: int
    lesson_id: int
    kind: ReminderKind
    send_at: datetime
    status: ReminderStatus
    attempts: int
    sent_at: datetime | None
    message_id: int | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, reminder: Reminder) -> Self:
        return cls(
            id=reminder.id,
            club_id=reminder.club_id,
            lesson_id=reminder.lesson_id,
            kind=reminder.kind,
            send_at=reminder.send_at,
            status=reminder.status,
            attempts=reminder.attempts,
            sent_at=reminder.sent_at,
            message_id=reminder.message_id,
            error=reminder.error,
            created_at=reminder.created_at,
            updated_at=reminder.updated_at,
        )


class ReminderWithLessonDTO(ReminderDTO):
    lesson: LessonDTO

    # Separate name, not an override of from_orm_obj: the lesson must be loaded eagerly by the repository.
    @classmethod
    def from_orm_obj_with_lesson(cls, reminder: Reminder) -> Self:
        dto = ReminderDTO.from_orm_obj(reminder)
        return cls(**dto.model_dump(), lesson=LessonDTO.from_orm_obj(reminder.lesson))


class ReminderDraftPreview(BaseModel):
    lesson: LessonDraft = Field(description="The lesson as it is in the form, not necessarily saved")
    kind: ReminderKind = Field(description="Which message to show")
    send_at: Moment | None = Field(
        default=None,
        description="When it would go out; relative times are counted from it. Null or past: now",
    )
