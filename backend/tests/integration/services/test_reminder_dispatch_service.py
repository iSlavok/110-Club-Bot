from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.methods import SendMessage

from app.enums import ReminderKind, ReminderStatus
from app.services import ReminderDispatchService
from tests.factories import make_club, make_lesson, make_reminder
from tests.providers import ALERTS_CHAT_ID, DEFAULT_NOW

CHAT_ID = -100_555
TOPIC_ID = 17
STARTS_AT = DEFAULT_NOW + timedelta(hours=1)


@pytest.fixture
async def service(request_container) -> ReminderDispatchService:
    return await request_container.get(ReminderDispatchService)


@pytest.fixture
def sent_message(bot) -> MagicMock:
    bot.send_message.return_value = MagicMock(message_id=321)
    return bot.send_message


async def _due_reminder(db_session, *, club_overrides=None, lesson_overrides=None, **overrides):
    club = await make_club(db_session, **{"chat_id": CHAT_ID, "reminders_topic_id": TOPIC_ID, **(club_overrides or {})})
    lesson = await make_lesson(
        db_session, club, **{"title": "Кислоты", "starts_at": STARTS_AT, **(lesson_overrides or {})}
    )
    return await make_reminder(db_session, lesson, **{"send_at": DEFAULT_NOW, **overrides})


def _bad_request() -> TelegramBadRequest:
    return TelegramBadRequest(method=SendMessage(chat_id=CHAT_ID, text="x"), message="message thread not found")


def _alerts(bot) -> list[str]:
    return [call.args[1] for call in bot.send_message.call_args_list if call.args and call.args[0] == ALERTS_CHAT_ID]


async def test_lists_due_pending_reminders_soonest_first(service, db_session) -> None:
    later = await _due_reminder(db_session, send_at=DEFAULT_NOW)
    sooner = await _due_reminder(db_session, send_at=DEFAULT_NOW - timedelta(minutes=5))
    await _due_reminder(db_session, send_at=DEFAULT_NOW + timedelta(minutes=1))
    await _due_reminder(db_session, status=ReminderStatus.SENT, send_at=DEFAULT_NOW - timedelta(hours=1))

    assert await service.list_due_ids() == [sooner.id, later.id]


async def test_sends_to_the_reminders_topic(service, db_session, sent_message) -> None:
    reminder = await _due_reminder(db_session)

    await service.dispatch(reminder.id)

    kwargs = sent_message.call_args.kwargs
    assert (kwargs["chat_id"], kwargs["message_thread_id"]) == (CHAT_ID, TOPIC_ID)
    assert kwargs["text"].startswith("<b>Урок «Кислоты»</b>\nЧерез час")
    assert kwargs["link_preview_options"].is_disabled
    assert (reminder.status, reminder.sent_at, reminder.message_id, reminder.attempts) == (
        ReminderStatus.SENT,
        DEFAULT_NOW,
        321,
        1,
    )


async def test_reminder_not_yet_due_is_left_alone(service, db_session, bot) -> None:
    reminder = await _due_reminder(db_session, send_at=DEFAULT_NOW + timedelta(minutes=1))

    await service.dispatch(reminder.id)

    bot.send_message.assert_not_called()
    assert reminder.status is ReminderStatus.PENDING


async def test_club_without_topic_fails_at_once_and_alerts(service, db_session, bot) -> None:
    reminder = await _due_reminder(db_session, club_overrides={"reminders_topic_id": None})

    await service.dispatch(reminder.id)

    assert reminder.status is ReminderStatus.FAILED
    assert reminder.error == "Club has no chat or reminders topic"
    [alert] = _alerts(bot)
    assert "«Кислоты» — напоминание об уроке" in alert
    assert bot.send_message.call_count == 1


async def test_inactive_club_is_skipped(service, db_session, bot) -> None:
    reminder = await _due_reminder(db_session, club_overrides={"is_active": False})

    await service.dispatch(reminder.id)

    assert reminder.status is ReminderStatus.SKIPPED
    bot.send_message.assert_not_called()


async def test_flood_limit_keeps_it_pending_and_postpones(service, db_session, bot) -> None:
    reminder = await _due_reminder(db_session)
    bot.send_message.side_effect = TelegramRetryAfter(
        method=SendMessage(chat_id=CHAT_ID, text="x"),
        message="Too Many Requests",
        retry_after=30,
    )

    await service.dispatch(reminder.id)

    assert reminder.status is ReminderStatus.PENDING
    assert reminder.send_at == DEFAULT_NOW + timedelta(seconds=30)
    assert reminder.attempts == 0


async def test_telegram_errors_fail_it_after_three_attempts_with_one_alert(service, db_session, bot, clock) -> None:
    reminder = await _due_reminder(db_session)
    bot.send_message.side_effect = _raise_unless_alert

    for minute in range(3):
        clock.set(DEFAULT_NOW + timedelta(minutes=minute))
        await service.dispatch(reminder.id)
        if minute < 2:
            assert (reminder.status, reminder.attempts) == (ReminderStatus.PENDING, minute + 1)

    assert (reminder.status, reminder.attempts) == (ReminderStatus.FAILED, 3)
    assert reminder.error == "Telegram server says - message thread not found"
    [alert] = _alerts(bot)
    assert "Ошибка: Telegram server says - message thread not found" in alert


def _raise_unless_alert(*args, **kwargs) -> MagicMock:
    if args and args[0] == ALERTS_CHAT_ID:
        return MagicMock(message_id=1)
    raise _bad_request()


@pytest.mark.parametrize(
    "case",
    [
        (ReminderKind.LESSON_UPCOMING, {"starts_at": DEFAULT_NOW - timedelta(minutes=6)}, None),
        (ReminderKind.LESSON_STARTING, {"starts_at": DEFAULT_NOW - timedelta(minutes=6)}, None),
        (ReminderKind.HOMEWORK_DEADLINE, {"homework_deadline_at": DEFAULT_NOW - timedelta(seconds=1)}, None),
        (ReminderKind.HOMEWORK_DEADLINE, {"homework_deadline_at": None}, None),
        (ReminderKind.LESSON_RESCHEDULED, {}, timedelta(minutes=61)),
        (ReminderKind.LESSON_CANCELLED, {"is_cancelled": True}, timedelta(minutes=61)),
        (ReminderKind.LESSON_UPCOMING, {"is_cancelled": True}, None),
        (ReminderKind.HOMEWORK_DEADLINE_CHANGED, {"homework_deadline_at": None}, None),
    ],
)
async def test_stale_reminders_are_skipped(service, db_session, bot, case) -> None:
    kind, lesson_overrides, late_by = case
    send_at = DEFAULT_NOW - (late_by or timedelta(minutes=10))
    reminder = await _due_reminder(db_session, kind=kind, send_at=send_at, lesson_overrides=lesson_overrides)

    await service.dispatch(reminder.id)

    assert reminder.status is ReminderStatus.SKIPPED
    bot.send_message.assert_not_called()


@pytest.mark.parametrize(
    ("kind", "lesson_overrides"),
    [
        (ReminderKind.LESSON_STARTING, {"starts_at": DEFAULT_NOW - timedelta(minutes=4)}),
        (ReminderKind.LESSON_CANCELLED, {"is_cancelled": True}),
        (ReminderKind.HOMEWORK_REMOVED, {"homework_deadline_at": None}),
    ],
)
async def test_slightly_late_reminders_still_go_out(service, db_session, sent_message, kind, lesson_overrides) -> None:
    reminder = await _due_reminder(
        db_session,
        kind=kind,
        send_at=DEFAULT_NOW - timedelta(minutes=30),
        lesson_overrides=lesson_overrides,
    )

    await service.dispatch(reminder.id)

    assert reminder.status is ReminderStatus.SENT
    sent_message.assert_called_once()


async def test_recorded_failures_fail_it_after_three(service, db_session, bot) -> None:
    reminder = await _due_reminder(db_session)

    for _ in range(3):
        await service.record_failure(reminder.id, "RuntimeError('boom')")

    assert (reminder.status, reminder.attempts, reminder.error) == (ReminderStatus.FAILED, 3, "RuntimeError('boom')")
    assert len(_alerts(bot)) == 1


async def test_recorded_failure_ignores_reminders_no_longer_pending(service, db_session) -> None:
    reminder = await _due_reminder(db_session, status=ReminderStatus.SENT)

    await service.record_failure(reminder.id, "late crash")

    assert (reminder.status, reminder.attempts) == (ReminderStatus.SENT, 0)
