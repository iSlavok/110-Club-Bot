from datetime import timedelta

import pytest
from sqlalchemy import select

from app.enums import Permission, ReminderKind, ReminderStatus
from app.models import Reminder
from tests.factories import make_admin_user, make_club, make_lesson, make_message, make_reminder, make_role
from tests.providers import DEFAULT_NOW

P = Permission
LATER = DEFAULT_NOW + timedelta(hours=3)


@pytest.fixture
async def sender(db_session):
    return await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW, P.MESSAGES_SEND))


@pytest.fixture
async def club(db_session):
    return await make_club(db_session, chat_id=-100_777, reminders_topic_id=5)


async def test_message_is_sent_right_away_by_default(api_client, login_as, db_session, sender, club) -> None:
    await login_as(sender)

    response = await api_client.post(
        f"/api/v1/clubs/{club.id}/messages",
        json={"text": "<strong>Привет!</strong>\nЗапись & ДЗ уже на платформе"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "lesson": None,
        "kind": "message",
        "text": "<b>Привет!</b>\nЗапись &amp; ДЗ уже на платформе",
        "send_at": "2026-10-01T09:00:00Z",
        "status": "pending",
        "attempts": 0,
        "sent_at": None,
        "error": None,
    }
    saved = await db_session.get(Reminder, body["id"])
    assert (saved.club_id, saved.lesson_id, saved.kind) == (club.id, None, ReminderKind.MESSAGE)


async def test_message_can_be_scheduled(api_client, login_as, sender, club) -> None:
    await login_as(sender)

    response = await api_client.post(
        f"/api/v1/clubs/{club.id}/messages",
        json={"text": "Скоро созвон", "send_at": LATER.isoformat()},
    )

    assert response.json()["send_at"] == "2026-10-01T12:00:00Z"


async def test_message_in_the_past_is_refused(api_client, login_as, sender, club) -> None:
    await login_as(sender)

    response = await api_client.post(
        f"/api/v1/clubs/{club.id}/messages",
        json={"text": "Опоздали", "send_at": DEFAULT_NOW.isoformat()},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "CLUB_MESSAGE_SEND_TIME_PASSED"


@pytest.mark.parametrize("text", ["", "<p>абзац</p>", "строка<br>строка", '<a href="javascript:x">x</a>'])
async def test_text_outside_telegram_html_is_refused(api_client, login_as, sender, club, text) -> None:
    await login_as(sender)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/messages", json={"text": text})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"
    assert response.json()["fields"][0]["loc"] == ["body", "text"]


@pytest.mark.parametrize(
    "club_overrides",
    [{"is_active": False}, {"reminders_topic_id": None}, {"chat_id": None}],
    ids=["inactive", "no-topic", "no-chat"],
)
async def test_club_the_bot_cannot_post_to_is_refused(api_client, login_as, db_session, sender, club_overrides) -> None:
    club = await make_club(db_session, **{"chat_id": -100_777, "reminders_topic_id": 5, **club_overrides})
    await login_as(sender)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/messages", json={"text": "Привет"})

    assert response.status_code == 409
    assert response.json()["code"] == "CLUB_NOT_REACHABLE"


async def test_unknown_club_is_not_found(api_client, login_as, sender) -> None:
    await login_as(sender)

    response = await api_client.post("/api/v1/clubs/999999/messages", json={"text": "Привет"})

    assert response.status_code == 404
    assert response.json()["code"] == "CLUB_NOT_FOUND"


async def test_lesson_editors_cannot_send_messages(api_client, login_as, db_session, club) -> None:
    editor = await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW, P.LESSONS_EDIT))
    message = await make_message(db_session, club, send_at=LATER)
    await login_as(editor)

    created = await api_client.post(f"/api/v1/clubs/{club.id}/messages", json={"text": "Привет"})
    changed = await api_client.patch(f"/api/v1/messages/{message.id}", json={"text": "Пока"})
    cancelled = await api_client.post(f"/api/v1/messages/{message.id}/cancel")
    cancelled_as_reminder = await api_client.post(f"/api/v1/reminders/{message.id}/cancel")

    assert [created.status_code, changed.status_code, cancelled.status_code] == [403, 403, 403]
    assert cancelled_as_reminder.status_code == 404
    assert message.status is ReminderStatus.PENDING


async def test_messages_are_listed_with_reminders(api_client, login_as, db_session, club) -> None:
    viewer = await make_admin_user(db_session, await make_role(db_session, P.LESSONS_VIEW))
    message = await make_message(db_session, club, text="<i>Привет</i>", send_at=LATER)
    await login_as(viewer)

    listed = await api_client.get(f"/api/v1/clubs/{club.id}/reminders")
    preview = await api_client.get(f"/api/v1/reminders/{message.id}/preview")

    assert [(item["kind"], item["lesson"], item["text"]) for item in listed.json()["items"]] == [
        ("message", None, "<i>Привет</i>"),
    ]
    assert preview.json() == {"html": "<i>Привет</i>"}


async def test_pending_message_can_be_changed(api_client, login_as, db_session, sender, club) -> None:
    message = await make_message(db_session, club, send_at=LATER)
    await login_as(sender)

    retimed = await api_client.patch(
        f"/api/v1/messages/{message.id}",
        json={"text": "<u>Новый</u> текст", "send_at": (LATER + timedelta(hours=1)).isoformat()},
    )
    now = await api_client.patch(f"/api/v1/messages/{message.id}", json={"send_at": None})

    assert retimed.status_code == 200
    assert (retimed.json()["text"], retimed.json()["send_at"]) == ("<u>Новый</u> текст", "2026-10-01T13:00:00Z")
    assert (now.json()["text"], now.json()["send_at"]) == ("<u>Новый</u> текст", "2026-10-01T09:00:00Z")


async def test_empty_change_is_refused(api_client, login_as, db_session, sender, club) -> None:
    message = await make_message(db_session, club, send_at=LATER)
    await login_as(sender)

    response = await api_client.patch(f"/api/v1/messages/{message.id}", json={})

    assert response.json()["code"] == "EMPTY_UPDATE"


async def test_pending_message_can_be_cancelled(api_client, login_as, db_session, sender, club) -> None:
    message = await make_message(db_session, club, send_at=LATER)
    await login_as(sender)

    response = await api_client.post(f"/api/v1/messages/{message.id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert message.status is ReminderStatus.CANCELLED


@pytest.mark.parametrize("status", [ReminderStatus.SENT, ReminderStatus.CANCELLED])
async def test_message_no_longer_pending_stays_as_is(api_client, login_as, db_session, sender, status) -> None:
    club = await make_club(db_session)
    message = await make_message(db_session, club, send_at=DEFAULT_NOW - timedelta(hours=1), status=status)
    await login_as(sender)

    changed = await api_client.patch(f"/api/v1/messages/{message.id}", json={"text": "Пока"})
    cancelled = await api_client.post(f"/api/v1/messages/{message.id}/cancel")

    assert [changed.status_code, cancelled.status_code] == [409, 409]
    assert changed.json()["code"] == "CLUB_MESSAGE_NOT_PENDING"


async def test_lesson_reminder_is_not_a_message(api_client, login_as, db_session, sender, club) -> None:
    lesson = await make_lesson(db_session, club, starts_at=LATER)
    reminder = await make_reminder(db_session, lesson)
    await login_as(sender)

    changed = await api_client.patch(f"/api/v1/messages/{reminder.id}", json={"text": "Пока"})
    cancelled = await api_client.post(f"/api/v1/messages/{reminder.id}/cancel")

    assert [changed.status_code, cancelled.status_code] == [404, 404]
    assert changed.json()["code"] == "CLUB_MESSAGE_NOT_FOUND"
    statement = select(Reminder.status).where(Reminder.id == reminder.id)
    assert await db_session.scalar(statement) is ReminderStatus.PENDING


async def test_draft_preview_has_no_message_kind(api_client, login_as, sender) -> None:
    await login_as(sender)

    response = await api_client.post(
        "/api/v1/reminders/preview",
        json={
            "lesson": {"kind": "lesson", "title": "Кислоты", "starts_at": LATER.isoformat()},
            "kind": "message",
        },
    )

    assert response.status_code == 422
