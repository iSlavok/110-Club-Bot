import html
import re
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from urllib.parse import urlsplit

from points_api import PointsAuthError, PointsClient, PointsError, PointsForbiddenError, PointsNotFoundError
from points_api.models import (
    ContentBlock,
    Course,
    CourseLessonSummary,
    DirectSpeechBlock,
    LessonBlock,
    LessonHomeworks,
    LessonPage,
    TextBlock,
    VideoBlock,
    WebinarBlock,
)

from app.clients.exceptions import PlatformAuthError, PlatformClientError, PlatformNotFoundError
from app.schemas import (
    PlatformCourse,
    PlatformHomework,
    PlatformHomeworkLevel,
    PlatformLesson,
    PlatformLessonBrief,
    PlatformLink,
    PlatformModule,
    PlatformNote,
)

PLATFORM_TIMEOUT_SECONDS = 10
# A curator call is a lesson with a Zoom meeting link; curators put it in any block, as text or a button.
_ZOOM_MEETING_LINK = re.compile(r"https?://(?:[\w-]+\.)*zoom\.(?:us|com)/(?:j|my|w|s|wc)/[^\s\"'<>]+")


@asynccontextmanager
async def open_points_platform_client(token: str) -> AsyncIterator["PointsPlatformClient"]:
    async with PointsClient(token, timeout=PLATFORM_TIMEOUT_SECONDS) as points:
        yield PointsPlatformClient(points)


# Read-only: the bot never changes anything on the platform.
class PointsPlatformClient:
    def __init__(self, points: PointsClient) -> None:
        self._points = points

    async def get_course(self, course_id: int) -> PlatformCourse:
        course = await _translated(self._points.get_course(course_id))
        return _course(course)

    async def get_lesson(self, lesson_id: int) -> PlatformLesson:
        page = await _translated(self._points.get_lesson(lesson_id))
        return _lesson(page)


async def _translated[T](request: Awaitable[T]) -> T:
    try:
        return await request
    except (PointsAuthError, PointsForbiddenError) as error:
        raise PlatformAuthError(str(error)) from error
    except PointsNotFoundError as error:
        raise PlatformNotFoundError(str(error)) from error
    except PointsError as error:
        raise PlatformClientError(str(error)) from error


def _course(course: Course) -> PlatformCourse:
    return PlatformCourse(
        id=course.id,
        title=course.title,
        modules=[
            PlatformModule(
                id=module.id,
                title=module.title,
                lessons=[_lesson_brief(lesson) for lesson in _ordered(module.lessons)],
            )
            for module in course.modules
        ],
    )


def _lesson_brief(lesson: CourseLessonSummary) -> PlatformLessonBrief:
    return PlatformLessonBrief(
        id=lesson.id,
        title=lesson.title,
        is_published=lesson.status == "published",
        starts_at=_utc(lesson.start_at),
        ends_at=_utc(lesson.end_at),
    )


def _lesson(page: LessonPage) -> PlatformLesson:
    lesson = page.lesson
    blocks = _ordered(lesson.blocks)
    return PlatformLesson(
        id=lesson.id,
        title=lesson.title,
        course_title=lesson.course_title or "",
        module_title=lesson.module_title or "",
        is_published=lesson.status == "published",
        starts_at=_utc(lesson.start_at),
        ends_at=_utc(lesson.end_at),
        publish_at=_utc(lesson.publish_at),
        is_stop_lesson=lesson.stopping,
        call_url=_call_url(lesson.model_dump(mode="json")),
        homework=_homework(lesson.homeworks),
        webinar=[link for block in blocks if isinstance(block, WebinarBlock) for link in _webinar_links(block)],
        videos=[link for block in blocks if isinstance(block, VideoBlock) for link in _video_links(block)],
        materials=[link for block in blocks if isinstance(block, ContentBlock) for link in _materials(block)],
        notes=[note for block in blocks if (note := _note(block)) is not None],
    )


def _homework(homeworks: LessonHomeworks | None) -> PlatformHomework | None:
    if homeworks is None:
        return None
    # The platform builds this sentence itself; with nothing set it is a bare ". ".
    summary = (homeworks.text or "").strip(" .")
    return PlatformHomework(
        deadline_at=_utc(homeworks.deadline),
        summary=summary or None,
        levels=[
            PlatformHomeworkLevel(
                title=level.difficulty_title or level.difficulty,
                is_required=level.is_required,
                is_trial=level.is_trial_task,
                time_limit_seconds=level.max_time_seconds or None,
                task_count=level.task_count,
            )
            for level in homeworks.difficulties
        ],
    )


def _webinar_links(block: WebinarBlock) -> list[PlatformLink]:
    data = block.data
    sources = (("Kinescope", data.kinescope_link), ("YouTube", data.youtube_link), ("Rutube", data.rutube_link))
    links = [PlatformLink(title=title, url=url) for title, link in sources if (url := _url(link))]
    if not links and (url := _url(data.description)):
        links.append(PlatformLink(title=_host(url), url=url))
    return links


def _video_links(block: VideoBlock) -> list[PlatformLink]:
    url = _url(block.data.description)
    return [] if url is None else [PlatformLink(title=_host(url), url=url)]


def _materials(block: ContentBlock) -> list[PlatformLink]:
    files = [
        PlatformLink(title=file.name or _host(url), url=url) for file in block.data.files if (url := _url(file.link))
    ]
    links = [
        PlatformLink(title=link.description or _host(url), url=url)
        for link in block.data.links
        if (url := _url(link.link))
    ]
    return files + links


def _note(block: LessonBlock) -> PlatformNote | None:
    if isinstance(block, TextBlock):
        title, text = block.data.title, block.data.description
    elif isinstance(block, DirectSpeechBlock):
        title, text = None, block.data.description
    else:
        return None
    text = (text or "").strip()
    return PlatformNote(title=title or None, text=text) if text else None


# Searched in every string of the lesson, fields the client models do not describe included.
def _call_url(node: object) -> str | None:
    if isinstance(node, str):
        match = _ZOOM_MEETING_LINK.search(html.unescape(node))
        return None if match is None else match.group().rstrip(".,;:!?)")
    if isinstance(node, dict):
        children = list(node.values())
    elif isinstance(node, list):
        children = node
    else:
        return None
    return next((url for child in children if (url := _call_url(child)) is not None), None)


# Same order as the platform shows: by order_id, items without one last.
def _ordered[T: (CourseLessonSummary, LessonBlock)](items: list[T]) -> list[T]:
    return sorted(items, key=lambda item: (item.order_id is None, item.order_id or 0, item.id))


def _utc(moment: datetime | None) -> datetime | None:
    return None if moment is None else moment.astimezone(UTC)


def _url(value: str | None) -> str | None:
    value = (value or "").strip()
    return value if urlsplit(value).scheme in {"http", "https"} else None


def _host(url: str) -> str:
    return urlsplit(url).hostname or url
