import sys
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

import httpx
import pytest
from points_api import PointsClient
from pydantic import SecretStr

from app.clients import (
    DisabledPlatformClient,
    PlatformAuthError,
    PlatformClientError,
    PlatformNotConfiguredError,
    PlatformNotFoundError,
    open_platform_client,
)
from app.clients.points_platform_client import PointsPlatformClient
from app.config import PlatformSettings
from app.schemas import (
    PlatformCourse,
    PlatformHomework,
    PlatformHomeworkLevel,
    PlatformLessonBrief,
    PlatformLink,
    PlatformModule,
    PlatformNote,
)

type Responder = Callable[[httpx.Request], httpx.Response]

COURSE = {
    "id": 7,
    "title": "Годовой курс",
    "type": "annual",
    "modules": [
        {
            "id": 70,
            "title": "1 блок",
            "lessons": [
                {
                    "id": 702,
                    "title": "Урок 1",
                    "status": "draft",
                    "type": "default",
                    "order_id": 2,
                    "start_at": "13.10.2026 19:00:00",
                },
                {
                    "id": 701,
                    "title": "Инфо о курсе",
                    "status": "published",
                    "type": "default",
                    "order_id": 1,
                    "start_at": None,
                },
            ],
        },
    ],
}
LESSON = {
    "lesson": {
        "id": 702,
        "title": "Урок 1",
        "course_title": "Годовой курс",
        "module_title": "1 блок",
        "status": "published",
        "type": "default",
        "start_at": "13.10.2026 19:00:00",
        "end_at": "13.10.2026 21:00:00",
        "publish_at": None,
        "stopping": True,
        "homeworks": {
            "deadline": "16.10.2026 23:59",
            "text": "Выполни базовый уровень до 16.10.2026 23:59. ",
            "difficulties": [
                {
                    "id": 1,
                    "difficulty": "simple",
                    "difficulty_title": "Базовый уровень",
                    "is_required": True,
                    "is_trial_task": True,
                    "max_time_seconds": 10800,
                    "task_count": 12,
                },
                {
                    "id": 2,
                    "difficulty": "hard",
                    "difficulty_title": "Сложный уровень",
                    "is_required": False,
                    "is_trial_task": False,
                    "max_time_seconds": 0,
                    "task_count": 5,
                },
            ],
        },
        "blocks": [
            {
                "id": 3,
                "type_id": "content",
                "order_id": 3,
                "data": {
                    "id": 30,
                    "files": [{"id": 31, "name": "Конспект.pdf", "link": "https://files.example.com/a.pdf"}],
                    "links": [{"description": "", "link": "https://video.example.com/cut"}, {"link": "javascript:x"}],
                },
            },
            {
                "id": 1,
                "type_id": "webinar",
                "order_id": 1,
                "data": {"id": 10, "kinescope_link": "https://kinescope.example.com/1", "youtube_link": None},
            },
            {"id": 2, "type_id": "direct_speech", "order_id": 2, "data": {"id": 20, "description": "Запись ниже"}},
            {
                "id": 4,
                "type_id": "text",
                "order_id": None,
                "data": {"id": 40, "title": "Привет!", "description": "Решай"},
            },
            {
                "id": 5,
                "type_id": "video",
                "order_id": 4,
                "data": {"id": 50, "description": "https://video.example.com/full"},
            },
            {"id": 6, "type_id": "homework", "order_id": 5, "data": {"id": 60}},
        ],
    },
}


class Recorder:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.responder: Responder = lambda _: httpx.Response(200, json=COURSE)

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.responder(request)


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
async def client(recorder: Recorder) -> AsyncIterator[PointsPlatformClient]:
    async with httpx.AsyncClient(transport=httpx.MockTransport(recorder.handle)) as http:
        yield PointsPlatformClient(PointsClient("platform-token", http=http))


async def test_course_lessons_come_in_platform_order_with_moscow_times(client) -> None:
    course = await client.get_course(7)

    assert course == PlatformCourse(
        id=7,
        title="Годовой курс",
        modules=[
            PlatformModule(
                id=70,
                title="1 блок",
                lessons=[
                    PlatformLessonBrief(id=701, title="Инфо о курсе", is_published=True, starts_at=None, ends_at=None),
                    PlatformLessonBrief(
                        id=702,
                        title="Урок 1",
                        is_published=False,
                        starts_at=datetime(2026, 10, 13, 16, 0, tzinfo=UTC),
                        ends_at=None,
                    ),
                ],
            ),
        ],
    )


async def test_lesson_card_has_homework_links_and_texts(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(200, json=LESSON)

    lesson = await client.get_lesson(702)

    assert (lesson.title, lesson.module_title, lesson.is_published, lesson.is_stop_lesson) == (
        "Урок 1",
        "1 блок",
        True,
        True,
    )
    assert (lesson.starts_at, lesson.ends_at, lesson.publish_at) == (
        datetime(2026, 10, 13, 16, 0, tzinfo=UTC),
        datetime(2026, 10, 13, 18, 0, tzinfo=UTC),
        None,
    )
    assert lesson.homework == PlatformHomework(
        deadline_at=datetime(2026, 10, 16, 20, 59, tzinfo=UTC),
        summary="Выполни базовый уровень до 16.10.2026 23:59",
        levels=[
            PlatformHomeworkLevel(
                title="Базовый уровень",
                is_required=True,
                is_trial=True,
                time_limit_seconds=10800,
                task_count=12,
            ),
            PlatformHomeworkLevel(
                title="Сложный уровень",
                is_required=False,
                is_trial=False,
                time_limit_seconds=None,
                task_count=5,
            ),
        ],
    )
    assert lesson.webinar == [PlatformLink(title="Kinescope", url="https://kinescope.example.com/1")]
    assert lesson.videos == [PlatformLink(title="video.example.com", url="https://video.example.com/full")]
    assert lesson.materials == [
        PlatformLink(title="Конспект.pdf", url="https://files.example.com/a.pdf"),
        PlatformLink(title="video.example.com", url="https://video.example.com/cut"),
    ]
    assert lesson.notes == [PlatformNote(title=None, text="Запись ниже"), PlatformNote(title="Привет!", text="Решай")]
    assert lesson.call_url is None


@pytest.mark.parametrize(
    ("block", "call_url"),
    [
        (
            {
                "type_id": "text",
                "data": {
                    "id": 1,
                    "description": "Созвон по ссылке\nhttps://us06web.zoom.us/j/1234567?pwd=abc. До встречи",
                },
            },
            "https://us06web.zoom.us/j/1234567?pwd=abc",
        ),
        (
            {
                "type_id": "text",
                "data": {"id": 1, "description": '<a href="https://zoom.us/j/1234567?pwd=a&amp;uname=b">Войти</a>'},
            },
            "https://zoom.us/j/1234567?pwd=a&uname=b",
        ),
        (
            {
                "type_id": "content",
                "data": {"id": 1, "links": [{"description": "Созвон", "link": "https://example.zoom.us/my/curator"}]},
            },
            "https://example.zoom.us/my/curator",
        ),
        ({"type_id": "text", "data": {"id": 1, "description": "Скачай клиент: https://zoom.us/download"}}, None),
        ({"type_id": "text", "data": {"id": 1, "description": "https://notzoom.us/j/1234567"}}, None),
        (
            {"type_id": "poll", "data": {"id": 1, "question": "Встреча: https://zoom.us/j/7654321"}},
            "https://zoom.us/j/7654321",
        ),
    ],
    ids=["text", "html-button", "content-link", "not-a-meeting", "other-host", "undescribed-block"],
)
async def test_zoom_meeting_link_anywhere_makes_a_call(client, recorder, block, call_url) -> None:
    lesson = {**LESSON["lesson"], "blocks": [{"id": 9, "order_id": 1, **block}]}
    recorder.responder = lambda _: httpx.Response(200, json={"lesson": lesson})

    result = await client.get_lesson(702)

    assert result.call_url == call_url


async def test_lesson_without_homework(client, recorder) -> None:
    lesson = {**LESSON["lesson"], "homeworks": None, "blocks": []}
    recorder.responder = lambda _: httpx.Response(200, json={"lesson": lesson})

    result = await client.get_lesson(702)

    assert result.homework is None


async def test_homework_with_nothing_set_has_no_summary(client, recorder) -> None:
    homework = {"deadline": None, "text": ". ", "difficulties": []}
    lesson = {**LESSON["lesson"], "homeworks": homework}
    recorder.responder = lambda _: httpx.Response(200, json={"lesson": lesson})

    result = await client.get_lesson(702)

    assert result.homework == PlatformHomework(deadline_at=None, summary=None, levels=[])


@pytest.mark.parametrize(
    "response",
    [httpx.Response(401), httpx.Response(403), httpx.Response(200, headers={"Location": "/captcha"}, json={})],
    ids=["401", "403", "captcha"],
)
async def test_refused_token_is_an_auth_error(client, recorder, response) -> None:
    recorder.responder = lambda _: response

    with pytest.raises(PlatformAuthError):
        await client.get_course(7)


async def test_missing_course_is_not_found(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(404)

    with pytest.raises(PlatformNotFoundError):
        await client.get_course(7)


@pytest.mark.parametrize(
    "responder",
    [
        lambda _: httpx.Response(500),
        lambda _: httpx.Response(200, text="<html>"),
        lambda _: httpx.Response(200, json=[]),
        lambda _: httpx.Response(200, json={"id": 7}),
        lambda _: httpx.Response(200, json={**COURSE, "modules": [{**COURSE["modules"][0], "lessons": [{"id": 1}]}]}),
    ],
    ids=["server-error", "not-json", "not-object", "no-modules", "broken-lesson"],
)
async def test_broken_answers_are_client_errors(client, recorder, responder) -> None:
    recorder.responder = responder

    with pytest.raises(PlatformClientError):
        await client.get_course(7)


async def test_network_failure_is_a_client_error(client, recorder) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    recorder.responder = fail

    with pytest.raises(PlatformClientError):
        await client.get_lesson(702)


async def test_without_a_token_the_platform_is_off() -> None:
    async with open_platform_client(PlatformSettings()) as client:
        assert isinstance(client, DisabledPlatformClient)


async def test_without_the_client_package_the_platform_is_off(monkeypatch) -> None:
    monkeypatch.delitem(sys.modules, "app.clients.points_platform_client")
    monkeypatch.setitem(sys.modules, "points_api", None)

    async with open_platform_client(PlatformSettings(token=SecretStr("platform-token"))) as client:
        assert isinstance(client, DisabledPlatformClient)


async def test_with_a_token_and_the_package_the_platform_is_on() -> None:
    async with open_platform_client(PlatformSettings(token=SecretStr("platform-token"))) as client:
        assert isinstance(client, PointsPlatformClient)


async def test_disabled_client_refuses_everything() -> None:
    client = DisabledPlatformClient()

    with pytest.raises(PlatformNotConfiguredError):
        await client.get_course(7)
    with pytest.raises(PlatformNotConfiguredError):
        await client.get_lesson(702)
