from datetime import datetime

from pydantic import BaseModel

from app.enums import LessonKind


class ScheduleItem(BaseModel):
    moment: datetime
    lesson_kind: LessonKind
    lesson_title: str
    is_homework_deadline: bool


class ClubSchedule(BaseModel):
    club_title: str
    block_title: str
    items: list[ScheduleItem]
