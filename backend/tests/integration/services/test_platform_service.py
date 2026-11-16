from datetime import timedelta

import pytest

from app.clients import PlatformAuthError, PlatformClientError
from app.exceptions import (
    ClubHasNoPlatformCourseError,
    ClubNotFoundError,
    PlatformCourseNotFoundError,
    PlatformLessonNotFoundError,
    PlatformLinkingDisabledError,
    PlatformTokenRejectedError,
    PlatformUnavailableError,
)
from app.schemas import LinkedLesson, PlatformCourse, PlatformLesson, PlatformLessonBrief, PlatformModule
from app.services import PlatformService
from tests.factories import make_club, make_lesson
from tests.providers import ALERTS_CHAT_ID, DEFAULT_NOW

COURSE_ID = 7


def _brief(lesson_id: int, *, days: int | None = None) -> PlatformLessonBrief:
    starts_at = None if days is None else DEFAULT_NOW + timedelta(days=days)
    return PlatformLessonBrief(
        id=lesson_id,
        title=f"Урок {lesson_id}",
        is_published=True,
        starts_at=starts_at,
        ends_at=None,
    )


def _course(*modules: list[PlatformLessonBrief]) -> PlatformCourse:
    return PlatformCourse(
        id=COURSE_ID,
        title="Годовой курс",
        modules=[
            PlatformModule(id=index, title=f"{index} блок", lessons=lessons)
            for index, lessons in enumerate(modules, start=1)
        ],
    )


def _lesson(lesson_id: int) -> PlatformLesson:
    return PlatformLesson(
        id=lesson_id,
        title=f"Урок {lesson_id}",
        course_title="Годовой курс",
        module_title="1 блок",
        is_published=True,
        starts_at=DEFAULT_NOW,
        ends_at=None,
        publish_at=None,
        is_stop_lesson=False,
        call_url=None,
        homework=None,
        webinar=[],
        videos=[],
        materials=[],
        notes=[],
    )


@pytest.fixture
async def service(request_container) -> PlatformService:
    return await request_container.get(PlatformService)


@pytest.fixture
async def club(db_session):
    return await make_club(db_session, platform_course_id=COURSE_ID)


def _alerts(bot) -> list[str]:
    return [call.args[1] for call in bot.send_message.call_args_list if call.args and call.args[0] == ALERTS_CHAT_ID]


async def test_outline_marks_lessons_linked_in_this_club(service, db_session, platform, club) -> None:
    platform.courses[COURSE_ID] = _course([_brief(1), _brief(2)], [_brief(3)])
    lesson = await make_lesson(db_session, club, title="Разбор", platform_lesson_id=2)
    call = await make_lesson(
        db_session,
        club,
        title="Созвон",
        starts_at=lesson.starts_at + timedelta(days=1),
        platform_lesson_id=2,
        is_cancelled=True,
    )
    await make_lesson(db_session, await make_club(db_session), platform_lesson_id=3)

    outline = await service.course_outline(club.id)

    assert [module.title for module in outline.modules] == ["1 блок", "2 блок"]
    linked = {option.lesson.id: option.linked for module in outline.modules for option in module.lessons}
    assert linked == {
        1: [],
        2: [
            LinkedLesson(id=lesson.id, title="Разбор", starts_at=lesson.starts_at, is_cancelled=False),
            LinkedLesson(id=call.id, title="Созвон", starts_at=call.starts_at, is_cancelled=True),
        ],
        3: [],
    }


async def test_suggests_the_lesson_after_the_last_linked_in_course_order(service, db_session, platform, club) -> None:
    platform.courses[COURSE_ID] = _course([_brief(1), _brief(2)], [_brief(3), _brief(4)])
    await make_lesson(db_session, club, platform_lesson_id=2)
    await make_lesson(db_session, club, platform_lesson_id=1, starts_at=DEFAULT_NOW + timedelta(days=9))

    outline = await service.course_outline(club.id)

    assert outline.suggested_lesson_id == 3


async def test_suggests_the_last_lesson_when_it_is_linked(service, db_session, platform, club) -> None:
    platform.courses[COURSE_ID] = _course([_brief(1), _brief(2)])
    await make_lesson(db_session, club, platform_lesson_id=2)

    outline = await service.course_outline(club.id)

    assert outline.suggested_lesson_id == 2


@pytest.mark.parametrize(
    ("lessons", "suggested"),
    [
        ([_brief(1), _brief(2, days=-1), _brief(3, days=1), _brief(4, days=2)], 3),
        ([_brief(1), _brief(2, days=-1)], 2),
        ([], None),
    ],
    ids=["next-to-start", "all-past", "empty"],
)
async def test_with_nothing_linked_suggests_the_next_to_start(service, platform, club, lessons, suggested) -> None:
    platform.courses[COURSE_ID] = _course(lessons)

    outline = await service.course_outline(club.id)

    assert outline.suggested_lesson_id == suggested


async def test_club_without_a_course(service, db_session) -> None:
    club = await make_club(db_session)

    with pytest.raises(ClubHasNoPlatformCourseError):
        await service.course_outline(club.id)
    with pytest.raises(ClubNotFoundError):
        await service.course_outline(999_999)


async def test_unknown_course_and_lesson(service, club) -> None:
    with pytest.raises(PlatformCourseNotFoundError):
        await service.course_outline(club.id)
    with pytest.raises(PlatformLessonNotFoundError):
        await service.lesson(5)


async def test_lesson_card(service, platform) -> None:
    platform.lessons[5] = _lesson(5)

    assert await service.lesson(5) == _lesson(5)


async def test_refused_token_alerts_the_owner_once_and_then_the_recovery(service, platform, bot) -> None:
    platform.lessons[5] = _lesson(5)
    platform.error = PlatformAuthError("401")

    for _ in range(2):
        with pytest.raises(PlatformTokenRejectedError):
            await service.lesson(5)
    platform.error = None
    await service.lesson(5)
    await service.lesson(5)

    alerts = _alerts(bot)
    assert len(alerts) == 2
    assert "не принимает токен" in alerts[0]
    assert "PLATFORM_TOKEN" in alerts[0]
    assert "снова отвечает" in alerts[1]


async def test_failing_platform_alerts_with_the_error(service, platform, bot) -> None:
    platform.error = PlatformClientError("Platform request failed: 502 <bad gateway>")

    with pytest.raises(PlatformUnavailableError):
        await service.lesson(5)

    [alert] = _alerts(bot)
    assert "не отвечает" in alert
    assert "502 &lt;bad gateway&gt;" in alert


async def test_missing_lesson_means_the_platform_answers(service, platform_health, bot) -> None:
    platform_health.is_failing = True

    with pytest.raises(PlatformLessonNotFoundError):
        await service.lesson(5)

    assert not platform_health.is_failing
    assert len(_alerts(bot)) == 1


async def test_without_a_token_linking_is_off_without_alerts(service, platform, bot) -> None:
    platform.is_enabled = False

    with pytest.raises(PlatformLinkingDisabledError):
        await service.lesson(5)

    assert _alerts(bot) == []
