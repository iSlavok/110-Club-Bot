from datetime import timedelta

import pytest

from app.enums import Permission, ReminderKind, ReminderStatus
from tests.factories import make_admin_user, make_club, make_lesson, make_reminder, make_role
from tests.providers import DEFAULT_NOW

P = Permission
LESSON = {
    "kind": "lesson",
    "title": "Кислоты",
    "starts_at": "2026-10-03T19:00:00+03:00",
    "call_url": "https://meet.example.com/abc",
}


@pytest.fixture
async def editor(db_session):
    return await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW, P.LESSONS_EDIT))


@pytest.fixture
async def viewer(db_session):
    return await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW))


async def test_lesson_flow(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    await login_as(editor)

    created = await api_client.post(f"/api/v1/clubs/{club.id}/lessons", json=LESSON)
    lesson_id = created.json()["id"]
    patched = await api_client.patch(
        f"/api/v1/lessons/{lesson_id}",
        params={"notify_chat": "true"},
        json={"starts_at": "2026-10-04T19:00:00+03:00", "homework_deadline_at": "2026-10-06T23:59:00+03:00"},
    )
    fetched = await api_client.get(f"/api/v1/lessons/{lesson_id}")
    cancelled = await api_client.post(f"/api/v1/lessons/{lesson_id}/cancel", json={"notify_chat": True})
    reminders = await api_client.get(
        f"/api/v1/clubs/{club.id}/reminders",
        params={"lesson_id": lesson_id, "view": "all", "include_cancelled": "true"},
    )

    assert created.status_code == 201
    assert created.json() == {
        "id": lesson_id,
        "club_id": club.id,
        "kind": "lesson",
        "title": "Кислоты",
        "description": None,
        "starts_at": "2026-10-03T16:00:00Z",
        "call_url": "https://meet.example.com/abc",
        "is_cancelled": False,
        "reminder_offsets": [1440, 60, 0],
        "homework_deadline_at": None,
        "homework_reminder_offsets": [2880, 1440, 180],
    }
    assert patched.status_code == 200
    assert patched.json()["homework_deadline_at"] == "2026-10-06T20:59:00Z"
    assert fetched.json()["starts_at"] == "2026-10-04T16:00:00Z"
    assert cancelled.json()["is_cancelled"] is True
    # The unsent reschedule notice is cancelled with the lesson: only the cancellation goes out.
    assert {(item["kind"], item["status"]) for item in reminders.json()["items"]} >= {
        ("lesson_rescheduled", "cancelled"),
        ("lesson_cancelled", "pending"),
    }


async def test_viewer_reads_but_cannot_edit(api_client, login_as, db_session, viewer) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)
    await login_as(viewer)

    listed = await api_client.get(f"/api/v1/clubs/{club.id}/lessons")
    created = await api_client.post(f"/api/v1/clubs/{club.id}/lessons", json=LESSON)
    patched = await api_client.patch(f"/api/v1/lessons/{lesson.id}", json={"title": "x"})
    cancelled = await api_client.post(f"/api/v1/lessons/{lesson.id}/cancel", json={})

    assert listed.status_code == 200
    assert [response.status_code for response in (created, patched, cancelled)] == [403, 403, 403]
    assert created.json()["code"] == "PERMISSION_DENIED"


async def test_lessons_need_the_view_permission(api_client, login_as, db_session) -> None:
    club = await make_club(db_session)
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW)))

    response = await api_client.get(f"/api/v1/clubs/{club.id}/lessons")

    assert response.status_code == 403


async def test_feed_views(api_client, login_as, db_session, viewer) -> None:
    club = await make_club(db_session)
    for title, hours in (("past", -1), ("next", 1), ("later", 2)):
        await make_lesson(db_session, club, title=title, starts_at=DEFAULT_NOW + timedelta(hours=hours))
    await make_lesson(db_session, club, title="off", starts_at=DEFAULT_NOW + timedelta(hours=3), is_cancelled=True)
    await login_as(viewer)

    async def titles(**params) -> list[str]:
        response = await api_client.get(f"/api/v1/clubs/{club.id}/lessons", params=params)
        return [item["title"] for item in response.json()["items"]]

    assert await titles() == ["next", "later"]
    assert await titles(view="past") == ["past"]
    assert await titles(view="all") == ["later", "next", "past"]
    assert await titles(view="all", include_cancelled="true") == ["off", "later", "next", "past"]


@pytest.mark.parametrize(
    "body",
    [
        {**LESSON, "reminder_offsets": [60, 60]},
        {**LESSON, "reminder_offsets": [43_201]},
        {**LESSON, "homework_reminder_offsets": list(range(11))},
        {**LESSON, "call_url": "ftp://example.com"},
        {**LESSON, "kind": "webinar"},
    ],
)
async def test_invalid_lesson_fails_validation(api_client, login_as, db_session, editor, body) -> None:
    club = await make_club(db_session)
    await login_as(editor)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/lessons", json=body)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


async def test_cancelled_lesson_cannot_be_edited(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, is_cancelled=True)
    await login_as(editor)

    response = await api_client.patch(f"/api/v1/lessons/{lesson.id}", json={"title": "Новое"})

    assert response.status_code == 409
    assert response.json()["code"] == "LESSON_CANCELLED"


async def test_patch_without_notify_chat_queues_no_notice(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=DEFAULT_NOW + timedelta(days=2))
    await make_reminder(db_session, lesson, kind=ReminderKind.LESSON_UPCOMING, status=ReminderStatus.SENT)
    await login_as(editor)

    await api_client.patch(f"/api/v1/lessons/{lesson.id}", json={"starts_at": "2026-10-05T19:00:00+03:00"})
    response = await api_client.get(f"/api/v1/clubs/{club.id}/reminders", params={"view": "all"})

    assert [item["kind"] for item in response.json()["items"]] == ["lesson_upcoming"]


async def test_unknown_lesson_and_club(api_client, login_as, editor) -> None:
    await login_as(editor)

    lesson = await api_client.get("/api/v1/lessons/999999")
    club = await api_client.post("/api/v1/clubs/999999/lessons", json=LESSON)

    assert (lesson.status_code, lesson.json()["code"]) == (404, "LESSON_NOT_FOUND")
    assert (club.status_code, club.json()["code"]) == (404, "CLUB_NOT_FOUND")
