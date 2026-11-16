from collections import defaultdict
from collections.abc import Awaitable
from datetime import datetime

from loguru import logger

from app import texts
from app.clients import PlatformAuthError, PlatformClient, PlatformClientError, PlatformHealth, PlatformNotFoundError
from app.clients import PlatformNotConfiguredError as PlatformClientNotConfiguredError
from app.exceptions import (
    AppError,
    ClubHasNoPlatformCourseError,
    ClubNotFoundError,
    PlatformCourseNotFoundError,
    PlatformLessonNotFoundError,
    PlatformLinkingDisabledError,
    PlatformTokenRejectedError,
    PlatformUnavailableError,
)
from app.models import Lesson
from app.repositories import ClubRepository, LessonRepository
from app.schemas import (
    LinkedLesson,
    PlatformCourse,
    PlatformCourseOutline,
    PlatformLesson,
    PlatformLessonOption,
    PlatformModuleOutline,
)
from app.telegram import AdminAlerts
from app.utils import Clock


# Reads the 100points platform for the lesson form; reminders never call it, so a dead token only stops linking.
class PlatformService:
    def __init__(
        self,
        *,
        club_repository: ClubRepository,
        lesson_repository: LessonRepository,
        platform_client: PlatformClient,
        platform_health: PlatformHealth,
        admin_alerts: AdminAlerts,
        clock: Clock,
    ) -> None:
        self._club_repository = club_repository
        self._lesson_repository = lesson_repository
        self._platform_client = platform_client
        self._platform_health = platform_health
        self._admin_alerts = admin_alerts
        self._clock = clock

    async def course_outline(self, club_id: int) -> PlatformCourseOutline:
        club = await self._club_repository.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        if club.platform_course_id is None:
            raise ClubHasNoPlatformCourseError(club_id)
        course = await self._request(
            self._platform_client.get_course(club.platform_course_id),
            not_found=PlatformCourseNotFoundError(club.platform_course_id),
        )
        linked = await self._lesson_repository.list_linked_to_platform(club_id=club_id)
        return _outline(course, linked, now=self._clock.now())

    async def lesson(self, platform_lesson_id: int) -> PlatformLesson:
        return await self._request(
            self._platform_client.get_lesson(platform_lesson_id),
            not_found=PlatformLessonNotFoundError(platform_lesson_id),
        )

    async def _request[T](self, request: Awaitable[T], *, not_found: AppError) -> T:
        try:
            result = await request
        except PlatformNotFoundError:
            await self._recovered()
            raise not_found from None
        except PlatformClientNotConfiguredError:
            raise PlatformLinkingDisabledError from None
        except PlatformAuthError as error:
            logger.warning("Platform refused the token: {}", error)
            await self._failed(texts.alerts.platform_token_rejected())
            raise PlatformTokenRejectedError from error
        except PlatformClientError as error:
            logger.warning("Platform request failed: {}", error)
            await self._failed(texts.alerts.platform_failed(str(error)))
            raise PlatformUnavailableError from error
        await self._recovered()
        return result

    async def _failed(self, alert: str) -> None:
        if await self._platform_health.mark_failing():
            await self._admin_alerts.send(alert)

    async def _recovered(self) -> None:
        if await self._platform_health.mark_ok():
            await self._admin_alerts.send(texts.alerts.platform_recovered())


def _outline(course: PlatformCourse, linked: list[Lesson], *, now: datetime) -> PlatformCourseOutline:
    by_platform_id: defaultdict[int, list[LinkedLesson]] = defaultdict(list)
    for lesson in linked:
        if lesson.platform_lesson_id is not None:
            by_platform_id[lesson.platform_lesson_id].append(
                LinkedLesson(
                    id=lesson.id,
                    title=lesson.title,
                    starts_at=lesson.starts_at,
                    is_cancelled=lesson.is_cancelled,
                ),
            )
    modules = [
        PlatformModuleOutline(
            id=module.id,
            title=module.title,
            lessons=[
                PlatformLessonOption(lesson=lesson, linked=by_platform_id.get(lesson.id, []))
                for lesson in module.lessons
            ],
        )
        for module in course.modules
    ]
    return PlatformCourseOutline(
        id=course.id,
        title=course.title,
        modules=modules,
        suggested_lesson_id=_suggested_lesson_id(course, set(by_platform_id), now=now),
    )


# Lessons are linked in course order: the one after the last linked is likely next.
# With nothing linked yet, the first lesson that has not started.
def _suggested_lesson_id(course: PlatformCourse, linked_ids: set[int], *, now: datetime) -> int | None:
    lessons = [lesson for module in course.modules for lesson in module.lessons]
    if not lessons:
        return None
    linked_positions = [position for position, lesson in enumerate(lessons) if lesson.id in linked_ids]
    if linked_positions:
        return lessons[min(linked_positions[-1] + 1, len(lessons) - 1)].id
    upcoming = (lesson for lesson in lessons if lesson.starts_at is not None and lesson.starts_at >= now)
    return next(upcoming, lessons[-1]).id
