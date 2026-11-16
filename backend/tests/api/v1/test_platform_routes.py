from datetime import UTC, datetime

import pytest

from app.clients import PlatformAuthError
from app.enums import Permission
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
from tests.factories import make_admin_user, make_club, make_lesson, make_role

STARTS_AT = datetime(2026, 10, 13, 16, 0, tzinfo=UTC)
COURSE = PlatformCourse(
    id=7,
    title="Годовой курс",
    modules=[
        PlatformModule(
            id=70,
            title="1 блок",
            lessons=[
                PlatformLessonBrief(id=702, title="Урок 1", is_published=False, starts_at=STARTS_AT, ends_at=None)
            ],
        ),
    ],
)
LESSON = PlatformLesson(
    id=702,
    title="Урок 1",
    course_title="Годовой курс",
    module_title="1 блок",
    is_published=True,
    starts_at=STARTS_AT,
    ends_at=None,
    publish_at=None,
    is_stop_lesson=False,
    call_url=None,
    homework=PlatformHomework(
        deadline_at=None,
        summary="Выполни базовый уровень",
        levels=[
            PlatformHomeworkLevel(
                title="Базовый уровень",
                is_required=True,
                is_trial=False,
                time_limit_seconds=None,
                task_count=12,
            ),
        ],
    ),
    webinar=[PlatformLink(title="Kinescope", url="https://kinescope.example.com/1")],
    videos=[],
    materials=[PlatformLink(title="Конспект.pdf", url="https://files.example.com/a.pdf")],
    notes=[PlatformNote(title=None, text="Запись ниже")],
)


@pytest.fixture
async def editor(db_session):
    return await make_admin_user(db_session, await make_role(db_session, Permission.LESSONS_EDIT))


async def test_course_of_the_club_with_linked_lessons(api_client, login_as, db_session, platform, editor) -> None:
    platform.courses[7] = COURSE
    club = await make_club(db_session, platform_course_id=7)
    lesson = await make_lesson(db_session, club, title="Разбор", starts_at=STARTS_AT, platform_lesson_id=702)
    await login_as(editor)

    response = await api_client.get(f"/api/v1/clubs/{club.id}/platform-course")

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "title": "Годовой курс",
        "modules": [
            {
                "id": 70,
                "title": "1 блок",
                "lessons": [
                    {
                        "id": 702,
                        "title": "Урок 1",
                        "is_published": False,
                        "starts_at": "2026-10-13T16:00:00Z",
                        "ends_at": None,
                        "linked": [
                            {
                                "id": lesson.id,
                                "title": "Разбор",
                                "starts_at": "2026-10-13T16:00:00Z",
                                "is_cancelled": False,
                            },
                        ],
                    },
                ],
            },
        ],
        "suggested_lesson_id": 702,
    }


async def test_platform_lesson_card(api_client, login_as, platform, editor) -> None:
    platform.lessons[702] = LESSON
    await login_as(editor)

    response = await api_client.get("/api/v1/platform/lessons/702")

    assert response.status_code == 200
    assert response.json() == {
        "id": 702,
        "title": "Урок 1",
        "course_title": "Годовой курс",
        "module_title": "1 блок",
        "is_published": True,
        "starts_at": "2026-10-13T16:00:00Z",
        "ends_at": None,
        "publish_at": None,
        "is_stop_lesson": False,
        "call_url": None,
        "homework": {
            "deadline_at": None,
            "summary": "Выполни базовый уровень",
            "levels": [
                {
                    "title": "Базовый уровень",
                    "is_required": True,
                    "is_trial": False,
                    "time_limit_seconds": None,
                    "task_count": 12,
                },
            ],
        },
        "webinar": [{"title": "Kinescope", "url": "https://kinescope.example.com/1"}],
        "videos": [],
        "materials": [{"title": "Конспект.pdf", "url": "https://files.example.com/a.pdf"}],
        "notes": [{"title": None, "text": "Запись ниже"}],
    }


async def test_club_course_is_set_by_its_id(api_client, login_as, db_session) -> None:
    club = await make_club(db_session)
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.CLUBS_EDIT)))

    response = await api_client.patch(f"/api/v1/clubs/{club.id}", json={"platform_course_id": 7})

    assert response.status_code == 200
    assert response.json()["platform_course_id"] == 7


async def test_errors(api_client, login_as, db_session, platform, editor) -> None:
    club = await make_club(db_session)
    await login_as(editor)

    no_course = await api_client.get(f"/api/v1/clubs/{club.id}/platform-course")
    platform.error = PlatformAuthError("401")
    rejected = await api_client.get("/api/v1/platform/lessons/702")

    assert (no_course.status_code, no_course.json()["code"]) == (409, "CLUB_HAS_NO_PLATFORM_COURSE")
    assert (rejected.status_code, rejected.json()["code"]) == (502, "PLATFORM_TOKEN_REJECTED")


# The platform is only read through the lesson form: viewing lessons is not enough.
async def test_needs_the_lessons_edit_permission(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.LESSONS_VIEW)))

    response = await api_client.get("/api/v1/platform/lessons/702")

    assert response.status_code == 403
