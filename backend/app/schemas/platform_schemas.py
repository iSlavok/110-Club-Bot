from datetime import datetime

from pydantic import BaseModel


class PlatformLessonBrief(BaseModel):
    id: int
    title: str
    is_published: bool
    starts_at: datetime | None
    ends_at: datetime | None


class PlatformModule(BaseModel):
    id: int
    title: str
    lessons: list[PlatformLessonBrief]


class PlatformCourse(BaseModel):
    id: int
    title: str
    modules: list[PlatformModule]


class PlatformHomeworkLevel(BaseModel):
    title: str
    is_required: bool
    is_trial: bool
    time_limit_seconds: int | None
    task_count: int | None


class PlatformHomework(BaseModel):
    deadline_at: datetime | None
    summary: str | None
    levels: list[PlatformHomeworkLevel]


class PlatformLink(BaseModel):
    title: str
    url: str


class PlatformNote(BaseModel):
    title: str | None
    text: str


class PlatformLesson(BaseModel):
    id: int
    title: str
    course_title: str
    module_title: str
    is_published: bool
    starts_at: datetime | None
    ends_at: datetime | None
    publish_at: datetime | None
    is_stop_lesson: bool
    call_url: str | None
    homework: PlatformHomework | None
    webinar: list[PlatformLink]
    videos: list[PlatformLink]
    materials: list[PlatformLink]
    notes: list[PlatformNote]


class LinkedLesson(BaseModel):
    id: int
    title: str
    starts_at: datetime
    is_cancelled: bool


class PlatformLessonOption(BaseModel):
    lesson: PlatformLessonBrief
    linked: list[LinkedLesson]


class PlatformModuleOutline(BaseModel):
    id: int
    title: str
    lessons: list[PlatformLessonOption]


# The course as the lesson form offers it: where each platform lesson is linked and which one is likely next.
class PlatformCourseOutline(BaseModel):
    id: int
    title: str
    modules: list[PlatformModuleOutline]
    suggested_lesson_id: int | None
