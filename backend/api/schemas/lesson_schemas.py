from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import LessonKind, LessonView
from app.schemas import LessonDTO, PageParams


class LessonListParams(PageParams):
    view: LessonView = Field(
        default=LessonView.UPCOMING,
        description="upcoming: not started yet, soonest first; past: started, latest first; all: latest first",
    )
    include_cancelled: bool = Field(default=False, description="Also show cancelled lessons")


class LessonResponse(BaseModel):
    id: int = Field(description="Lesson id")
    club_id: int = Field(description="Club the lesson belongs to")
    kind: LessonKind = Field(description="Teacher's lesson or a call with the curator")
    title: str = Field(description="Lesson topic")
    description: str | None = Field(description="Shown in the reminders")
    starts_at: datetime = Field(description="Start time, UTC")
    call_url: str | None = Field(description="Link to the video call")
    is_cancelled: bool = Field(description="Cancelled lessons can no longer be changed")
    reminder_offsets: list[int] = Field(description="Minutes before the start to remind at, latest first")
    homework_deadline_at: datetime | None = Field(description="Homework deadline, UTC; null: no homework")
    homework_reminder_offsets: list[int] = Field(
        description="Minutes before the homework deadline to remind at, latest first",
    )

    @classmethod
    def from_dto(cls, lesson: LessonDTO) -> Self:
        return cls(
            id=lesson.id,
            club_id=lesson.club_id,
            kind=lesson.kind,
            title=lesson.title,
            description=lesson.description,
            starts_at=lesson.starts_at,
            call_url=lesson.call_url,
            is_cancelled=lesson.is_cancelled,
            reminder_offsets=lesson.reminder_offsets,
            homework_deadline_at=lesson.homework_deadline_at,
            homework_reminder_offsets=lesson.homework_reminder_offsets,
        )


class LessonCancelRequest(BaseModel):
    notify_chat: bool = Field(default=False, description="Tell the club chat that the lesson is cancelled")
