from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints

from app.enums import LessonKind
from app.models import Lesson
from app.models.lesson import CALL_URL_MAX_LEN, LESSON_TITLE_MAX_LEN
from app.schemas.club_schemas import Moment
from app.schemas.patch_schemas import Maybe, PatchSchema
from app.types import ReminderOffsets

# Keeps a reminder with the description under Telegram's 4096-character message limit.
LESSON_DESCRIPTION_MAX_LEN = 2000

type LessonTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=LESSON_TITLE_MAX_LEN),
]
type LessonDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=LESSON_DESCRIPTION_MAX_LEN),
]
# Goes into an href of the chat message: only plain http(s) links.
type CallUrl = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=CALL_URL_MAX_LEN, pattern=r"^https?://[^\s<>\"']+$"),
]


class LessonDTO(BaseModel):
    id: int
    club_id: int
    kind: LessonKind
    title: str
    description: str | None
    starts_at: datetime
    call_url: str | None
    is_cancelled: bool
    reminder_offsets: list[int]
    homework_deadline_at: datetime | None
    homework_reminder_offsets: list[int]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, lesson: Lesson) -> Self:
        return cls(
            id=lesson.id,
            club_id=lesson.club_id,
            kind=lesson.kind,
            title=lesson.title,
            description=lesson.description,
            starts_at=lesson.starts_at,
            call_url=lesson.call_url,
            is_cancelled=lesson.is_cancelled,
            reminder_offsets=list(lesson.reminder_offsets),
            homework_deadline_at=lesson.homework_deadline_at,
            homework_reminder_offsets=list(lesson.homework_reminder_offsets),
            created_at=lesson.created_at,
            updated_at=lesson.updated_at,
        )


class LessonCreate(BaseModel):
    kind: LessonKind = Field(description="Teacher's lesson or a call with the curator")
    title: LessonTitle = Field(description="Lesson topic")
    description: LessonDescription | None = Field(default=None, description="Shown in the reminders")
    starts_at: Moment = Field(description="Start time")
    call_url: CallUrl | None = Field(default=None, description="Link to the video call, http(s)")
    reminder_offsets: ReminderOffsets | None = Field(
        default=None,
        description="Minutes before the start to remind at, unique; 0 means at the start. Omitted: bot settings",
    )
    homework_deadline_at: Moment | None = Field(default=None, description="Homework deadline; null: no homework")
    homework_reminder_offsets: ReminderOffsets | None = Field(
        default=None,
        description="Minutes before the homework deadline to remind at, unique. Omitted: bot settings",
    )


class LessonUpdate(PatchSchema):
    kind: Maybe[LessonKind] = Field(description="Teacher's lesson or a call with the curator")
    title: Maybe[LessonTitle] = Field(description="Lesson topic")
    description: Maybe[LessonDescription | None] = Field(description="Shown in the reminders")
    starts_at: Maybe[Moment] = Field(description="Start time; a change replans the lesson reminders")
    call_url: Maybe[CallUrl | None] = Field(description="Link to the video call, http(s)")
    reminder_offsets: Maybe[ReminderOffsets] = Field(
        description="Minutes before the start to remind at, unique; 0 means at the start",
    )
    homework_deadline_at: Maybe[Moment | None] = Field(description="Homework deadline; null removes the homework")
    homework_reminder_offsets: Maybe[ReminderOffsets] = Field(
        description="Minutes before the homework deadline to remind at, unique",
    )
