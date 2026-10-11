from dataclasses import dataclass
from datetime import datetime
from typing import Self

from app.enums import LessonView, ReminderKind
from app.exceptions import ClubNotFoundError, EmptyUpdateError, LessonCancelledError, LessonNotFoundError
from app.models import Lesson
from app.repositories import ClubRepository, LessonRepository
from app.schemas import LessonCreate, LessonDTO, LessonUpdate, PageParams, Paginated
from app.services.app_settings_service import AppSettingsService
from app.services.reminder_planner import ReminderPlanner
from app.utils import Clock


@dataclass(frozen=True, slots=True)
class _Schedule:
    starts_at: datetime
    reminder_offsets: list[int]
    homework_deadline_at: datetime | None
    homework_reminder_offsets: list[int]

    @classmethod
    def of(cls, lesson: Lesson) -> Self:
        return cls(
            starts_at=lesson.starts_at,
            reminder_offsets=list(lesson.reminder_offsets),
            homework_deadline_at=lesson.homework_deadline_at,
            homework_reminder_offsets=list(lesson.homework_reminder_offsets),
        )

    def lesson_changed(self, other: Self) -> bool:
        return (self.starts_at, self.reminder_offsets) != (other.starts_at, other.reminder_offsets)

    def homework_changed(self, other: Self) -> bool:
        return (self.homework_deadline_at, self.homework_reminder_offsets) != (
            other.homework_deadline_at,
            other.homework_reminder_offsets,
        )

    # Adding homework sends nothing extra: its deadline reminders tell the chat anyway.
    def notices(self, new: Self) -> list[ReminderKind]:
        notices: list[ReminderKind] = []
        if new.starts_at != self.starts_at:
            notices.append(ReminderKind.LESSON_RESCHEDULED)
        if self.homework_deadline_at is not None:
            if new.homework_deadline_at is None:
                notices.append(ReminderKind.HOMEWORK_REMOVED)
            elif new.homework_deadline_at != self.homework_deadline_at:
                notices.append(ReminderKind.HOMEWORK_DEADLINE_CHANGED)
        return notices


class LessonService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        club_repository: ClubRepository,
        app_settings_service: AppSettingsService,
        reminder_planner: ReminderPlanner,
        clock: Clock,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._club_repository = club_repository
        self._app_settings_service = app_settings_service
        self._reminder_planner = reminder_planner
        self._clock = clock

    async def list_page(
        self,
        club_id: int,
        page: PageParams,
        *,
        view: LessonView,
        include_cancelled: bool,
    ) -> Paginated[LessonDTO]:
        await self._ensure_club_exists(club_id)
        lessons = await self._lesson_repository.list_page_for_club(
            club_id=club_id,
            view=view,
            include_cancelled=include_cancelled,
            now=self._clock.now(),
            limit=page.per_page,
            offset=page.offset,
        )
        return Paginated(items=[LessonDTO.from_orm_obj(lesson) for lesson in lessons.items], total=lessons.total)

    async def get(self, lesson_id: int) -> LessonDTO:
        lesson = await self._get(lesson_id)
        return LessonDTO.from_orm_obj(lesson)

    async def create(self, club_id: int, data: LessonCreate) -> LessonDTO:
        await self._ensure_club_exists(club_id)
        defaults = await self._app_settings_service.get()
        lesson = Lesson(
            club_id=club_id,
            kind=data.kind,
            title=data.title,
            description=data.description,
            starts_at=data.starts_at,
            call_url=data.call_url,
            reminder_offsets=_or_default(data.reminder_offsets, defaults.default_lesson_offsets),
            homework_deadline_at=data.homework_deadline_at,
            homework_reminder_offsets=_or_default(data.homework_reminder_offsets, defaults.default_homework_offsets),
        )
        self._lesson_repository.add(lesson)
        await self._lesson_repository.flush()
        self._reminder_planner.plan_lesson(lesson)
        self._reminder_planner.plan_homework(lesson)
        await self._lesson_repository.flush()
        return LessonDTO.from_orm_obj(lesson)

    async def update(self, lesson_id: int, patch: LessonUpdate, *, notify_chat: bool = False) -> LessonDTO:
        if patch.is_empty():
            raise EmptyUpdateError
        lesson = await self._get_editable(lesson_id)
        before = _Schedule.of(lesson)
        lesson.kind = patch.kind.apply(lesson.kind)
        lesson.title = patch.title.apply(lesson.title)
        lesson.description = patch.description.apply(lesson.description)
        lesson.starts_at = patch.starts_at.apply(lesson.starts_at)
        lesson.call_url = patch.call_url.apply(lesson.call_url)
        lesson.reminder_offsets = patch.reminder_offsets.apply(lesson.reminder_offsets)
        lesson.homework_deadline_at = patch.homework_deadline_at.apply(lesson.homework_deadline_at)
        lesson.homework_reminder_offsets = patch.homework_reminder_offsets.apply(lesson.homework_reminder_offsets)
        after = _Schedule.of(lesson)

        if before.lesson_changed(after):
            await self._reminder_planner.replan_lesson(lesson)
        if before.homework_changed(after):
            await self._reminder_planner.replan_homework(lesson)
        if notify_chat:
            for kind in before.notices(after):
                self._reminder_planner.notify_now(lesson, kind)
        await self._lesson_repository.flush()
        return LessonDTO.from_orm_obj(lesson)

    async def cancel(self, lesson_id: int, *, notify_chat: bool = False) -> LessonDTO:
        lesson = await self._get_editable(lesson_id)
        lesson.is_cancelled = True
        await self._reminder_planner.cancel_all(lesson)
        if notify_chat:
            self._reminder_planner.notify_now(lesson, ReminderKind.LESSON_CANCELLED)
        await self._lesson_repository.flush()
        return LessonDTO.from_orm_obj(lesson)

    async def _get(self, lesson_id: int) -> Lesson:
        lesson = await self._lesson_repository.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFoundError(lesson_id)
        return lesson

    async def _get_editable(self, lesson_id: int) -> Lesson:
        lesson = await self._get(lesson_id)
        if lesson.is_cancelled:
            raise LessonCancelledError
        return lesson

    async def _ensure_club_exists(self, club_id: int) -> None:
        if await self._club_repository.get_by_id(club_id) is None:
            raise ClubNotFoundError(club_id)


def _or_default(offsets: list[int] | None, default: list[int]) -> list[int]:
    return list(default) if offsets is None else offsets
