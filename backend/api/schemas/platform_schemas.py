from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.schemas import (
    LinkedLesson,
    PlatformCourseOutline,
    PlatformHomework,
    PlatformHomeworkLevel,
    PlatformLesson,
    PlatformLessonOption,
    PlatformLink,
    PlatformModuleOutline,
    PlatformNote,
)


class LinkedLessonResponse(BaseModel):
    id: int = Field(description="Club lesson linked to the platform lesson")
    title: str = Field(description="Lesson topic")
    starts_at: datetime = Field(description="Start time, UTC")
    is_cancelled: bool = Field(description="Whether the lesson is cancelled")

    @classmethod
    def from_dto(cls, lesson: LinkedLesson) -> Self:
        return cls(id=lesson.id, title=lesson.title, starts_at=lesson.starts_at, is_cancelled=lesson.is_cancelled)


class PlatformLessonOptionResponse(BaseModel):
    id: int = Field(description="Platform lesson id")
    title: str = Field(description="Lesson title on the platform")
    is_published: bool = Field(description="false: a draft students do not see")
    starts_at: datetime | None = Field(description="Start time, UTC; null when the platform has none")
    ends_at: datetime | None = Field(description="End time, UTC")
    linked: list[LinkedLessonResponse] = Field(description="Club lessons already linked to it, by start time")

    @classmethod
    def from_dto(cls, option: PlatformLessonOption) -> Self:
        lesson = option.lesson
        return cls(
            id=lesson.id,
            title=lesson.title,
            is_published=lesson.is_published,
            starts_at=lesson.starts_at,
            ends_at=lesson.ends_at,
            linked=[LinkedLessonResponse.from_dto(linked) for linked in option.linked],
        )


class PlatformModuleResponse(BaseModel):
    id: int = Field(description="Platform module id")
    title: str = Field(description="Module title, a block of the course")
    lessons: list[PlatformLessonOptionResponse] = Field(description="Lessons in the platform order")

    @classmethod
    def from_dto(cls, module: PlatformModuleOutline) -> Self:
        return cls(
            id=module.id,
            title=module.title,
            lessons=[PlatformLessonOptionResponse.from_dto(lesson) for lesson in module.lessons],
        )


class PlatformCourseResponse(BaseModel):
    id: int = Field(description="Platform course id")
    title: str = Field(description="Course title")
    modules: list[PlatformModuleResponse] = Field(description="Modules in the platform order")
    suggested_lesson_id: int | None = Field(
        description="Lesson after the last linked one, or the next to start when none is linked",
    )

    @classmethod
    def from_dto(cls, course: PlatformCourseOutline) -> Self:
        return cls(
            id=course.id,
            title=course.title,
            modules=[PlatformModuleResponse.from_dto(module) for module in course.modules],
            suggested_lesson_id=course.suggested_lesson_id,
        )


class PlatformLinkResponse(BaseModel):
    title: str = Field(description="File name, link caption or site")
    url: str = Field(description="http(s) link")

    @classmethod
    def from_dto(cls, link: PlatformLink) -> Self:
        return cls(title=link.title, url=link.url)


class PlatformNoteResponse(BaseModel):
    title: str | None = Field(description="Heading of a text block")
    text: str = Field(description="Plain text with line breaks")

    @classmethod
    def from_dto(cls, note: PlatformNote) -> Self:
        return cls(title=note.title, text=note.text)


class PlatformHomeworkLevelResponse(BaseModel):
    title: str = Field(description="Level, e.g. Базовый уровень")
    is_required: bool = Field(description="Students must do it")
    is_trial: bool = Field(description="A mock exam: the timer starts when it is opened")
    time_limit_seconds: int | None = Field(description="Time to do it; null: unlimited")
    task_count: int | None = Field(description="Tasks in it")

    @classmethod
    def from_dto(cls, level: PlatformHomeworkLevel) -> Self:
        return cls(
            title=level.title,
            is_required=level.is_required,
            is_trial=level.is_trial,
            time_limit_seconds=level.time_limit_seconds,
            task_count=level.task_count,
        )


class PlatformHomeworkResponse(BaseModel):
    deadline_at: datetime | None = Field(description="Deadline, UTC; null: none")
    summary: str | None = Field(description="What to do, as the platform tells students")
    levels: list[PlatformHomeworkLevelResponse] = Field(description="Homework levels")

    @classmethod
    def from_dto(cls, homework: PlatformHomework) -> Self:
        return cls(
            deadline_at=homework.deadline_at,
            summary=homework.summary,
            levels=[PlatformHomeworkLevelResponse.from_dto(level) for level in homework.levels],
        )


class PlatformLessonResponse(BaseModel):
    id: int = Field(description="Platform lesson id")
    title: str = Field(description="Lesson title on the platform")
    course_title: str = Field(description="Course title")
    module_title: str = Field(description="Module title")
    is_published: bool = Field(description="false: a draft students do not see")
    starts_at: datetime | None = Field(description="Start time, UTC")
    ends_at: datetime | None = Field(description="End time, UTC")
    publish_at: datetime | None = Field(description="When it opens to students, UTC")
    is_stop_lesson: bool = Field(description="Students cannot go further until they finish it")
    call_url: str | None = Field(description="Zoom link found anywhere in the lesson: the lesson is a call")
    homework: PlatformHomeworkResponse | None = Field(description="null: the lesson has no homework")
    webinar: list[PlatformLinkResponse] = Field(description="Webinar links")
    videos: list[PlatformLinkResponse] = Field(description="Video links")
    materials: list[PlatformLinkResponse] = Field(description="Files and links of the useful materials")
    notes: list[PlatformNoteResponse] = Field(description="Texts of the lesson blocks")

    @classmethod
    def from_dto(cls, lesson: PlatformLesson) -> Self:
        return cls(
            id=lesson.id,
            title=lesson.title,
            course_title=lesson.course_title,
            module_title=lesson.module_title,
            is_published=lesson.is_published,
            starts_at=lesson.starts_at,
            ends_at=lesson.ends_at,
            publish_at=lesson.publish_at,
            is_stop_lesson=lesson.is_stop_lesson,
            call_url=lesson.call_url,
            homework=None if lesson.homework is None else PlatformHomeworkResponse.from_dto(lesson.homework),
            webinar=[PlatformLinkResponse.from_dto(link) for link in lesson.webinar],
            videos=[PlatformLinkResponse.from_dto(link) for link in lesson.videos],
            materials=[PlatformLinkResponse.from_dto(link) for link in lesson.materials],
            notes=[PlatformNoteResponse.from_dto(note) for note in lesson.notes],
        )
