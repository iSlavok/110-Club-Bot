from datetime import timedelta

import pytest

from app.enums import Permission, ReminderKind, ReminderStatus
from tests.factories import make_admin_user, make_club, make_lesson, make_reminder, make_role
from tests.providers import DEFAULT_NOW

P = Permission


@pytest.fixture
async def editor(db_session):
    return await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW, P.LESSONS_EDIT))


async def test_reminder_row_shape(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, title="Кислоты", starts_at=DEFAULT_NOW + timedelta(hours=2))
    reminder = await make_reminder(db_session, lesson, send_at=DEFAULT_NOW + timedelta(hours=1))
    await login_as(editor)

    response = await api_client.get(f"/api/v1/clubs/{club.id}/reminders")

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": reminder.id,
            "lesson": {
                "id": lesson.id,
                "kind": "lesson",
                "title": "Кислоты",
                "starts_at": "2026-10-01T11:00:00Z",
                "is_cancelled": False,
            },
            "kind": "lesson_upcoming",
            "send_at": "2026-10-01T10:00:00Z",
            "status": "pending",
            "attempts": 0,
            "sent_at": None,
            "error": None,
        },
    ]


async def test_feed_views_and_order(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=DEFAULT_NOW + timedelta(days=3))
    other = await make_lesson(db_session, club, starts_at=DEFAULT_NOW + timedelta(days=3))

    async def reminder(name: str, hours: int, status: ReminderStatus, sent_hours: int | None = None, of=lesson):
        sent_at = DEFAULT_NOW + timedelta(hours=sent_hours) if sent_hours is not None else None
        made = await make_reminder(
            db_session,
            of,
            send_at=DEFAULT_NOW + timedelta(hours=hours),
            status=status,
            sent_at=sent_at,
        )
        return name, made.id

    rows = dict(
        [
            await reminder("pending-late", 5, ReminderStatus.PENDING),
            await reminder("pending-soon", 1, ReminderStatus.PENDING),
            await reminder("sent-old", -5, ReminderStatus.SENT, sent_hours=-5),
            await reminder("sent-new", -1, ReminderStatus.SENT, sent_hours=-1),
            await reminder("failed", -2, ReminderStatus.FAILED),
            await reminder("cancelled-ahead", 2, ReminderStatus.CANCELLED),
            await reminder("cancelled-past", -3, ReminderStatus.CANCELLED),
            await reminder("other-lesson", 3, ReminderStatus.PENDING, of=other),
        ],
    )
    names = {reminder_id: name for name, reminder_id in rows.items()}
    await login_as(editor)

    async def listed(**params) -> list[str]:
        response = await api_client.get(f"/api/v1/clubs/{club.id}/reminders", params=params)
        return [names[item["id"]] for item in response.json()["items"]]

    assert await listed() == ["pending-soon", "other-lesson", "pending-late"]
    assert await listed(include_cancelled="true") == ["pending-soon", "cancelled-ahead", "other-lesson", "pending-late"]
    assert await listed(view="sent") == ["sent-new", "sent-old"]
    assert await listed(view="all", lesson_id=lesson.id) == [
        "pending-late",
        "pending-soon",
        "sent-new",
        "failed",
        "sent-old",
    ]
    assert await listed(view="all", lesson_id=lesson.id, include_cancelled="true") == [
        "pending-late",
        "cancelled-ahead",
        "pending-soon",
        "sent-new",
        "failed",
        "cancelled-past",
        "sent-old",
    ]


async def test_preview_renders_the_message_as_it_will_go_out(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, title="Кислоты", starts_at=DEFAULT_NOW + timedelta(days=1, hours=1))
    reminder = await make_reminder(db_session, lesson, send_at=DEFAULT_NOW + timedelta(days=1))
    await login_as(editor)

    response = await api_client.get(f"/api/v1/reminders/{reminder.id}/preview")

    assert response.status_code == 200
    assert response.json() == {"html": "<b>Урок «Кислоты»</b>\nЧерез час, в 13:00 (МСК)"}


async def test_preview_of_a_sent_reminder_uses_its_send_time(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, title="Кислоты", starts_at=DEFAULT_NOW - timedelta(hours=1))
    reminder = await make_reminder(
        db_session,
        lesson,
        kind=ReminderKind.LESSON_STARTING,
        send_at=DEFAULT_NOW - timedelta(hours=1),
        status=ReminderStatus.SENT,
        sent_at=DEFAULT_NOW - timedelta(hours=1),
    )
    await login_as(editor)

    response = await api_client.get(f"/api/v1/reminders/{reminder.id}/preview")

    assert response.json() == {"html": "<b>Урок «Кислоты» начинается</b>"}


async def test_preview_of_a_reminder_about_removed_homework_is_refused(
    api_client, login_as, db_session, editor
) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, homework_deadline_at=None)
    reminder = await make_reminder(
        db_session,
        lesson,
        kind=ReminderKind.HOMEWORK_DEADLINE,
        status=ReminderStatus.CANCELLED,
    )
    await login_as(editor)

    response = await api_client.get(f"/api/v1/reminders/{reminder.id}/preview")

    assert response.status_code == 409
    assert response.json()["code"] == "REMINDER_PREVIEW_UNAVAILABLE"


async def test_cancel_only_pending(api_client, login_as, db_session, editor) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)
    pending = await make_reminder(db_session, lesson)
    sent = await make_reminder(db_session, lesson, status=ReminderStatus.SENT)
    await login_as(editor)

    cancelled = await api_client.post(f"/api/v1/reminders/{pending.id}/cancel")
    refused = await api_client.post(f"/api/v1/reminders/{sent.id}/cancel")

    assert (cancelled.status_code, cancelled.json()["status"]) == (200, "cancelled")
    assert (refused.status_code, refused.json()["code"]) == (409, "REMINDER_NOT_PENDING")


async def test_cancel_needs_edit_permission(api_client, login_as, db_session) -> None:
    club = await make_club(db_session)
    reminder = await make_reminder(db_session, await make_lesson(db_session, club))
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW)))

    response = await api_client.post(f"/api/v1/reminders/{reminder.id}/cancel")

    assert response.status_code == 403


async def test_unknown_reminder_and_club(api_client, login_as, editor) -> None:
    await login_as(editor)

    preview = await api_client.get("/api/v1/reminders/999999/preview")
    cancel = await api_client.post("/api/v1/reminders/999999/cancel")
    listed = await api_client.get("/api/v1/clubs/999999/reminders")

    assert [preview.json()["code"], cancel.json()["code"]] == ["REMINDER_NOT_FOUND", "REMINDER_NOT_FOUND"]
    assert listed.json()["code"] == "CLUB_NOT_FOUND"
