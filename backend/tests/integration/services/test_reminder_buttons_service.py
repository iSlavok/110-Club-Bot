from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import EditMessageReplyMarkup

from app.enums import LessonKind, ReminderKind, ReminderStatus
from app.services import ReminderButtonsService
from tests.factories import make_club, make_lesson, make_reminder
from tests.providers import DEFAULT_NOW

CHAT_ID = -100_555
CALL_URL = "https://meet.example.com/abc"
LESSON_URL = "https://lk.100points.ru/student/lesson/50002"
CALL_OVER = DEFAULT_NOW - timedelta(hours=3)


@pytest.fixture
async def service(request_container) -> ReminderButtonsService:
    return await request_container.get(ReminderButtonsService)


async def _sent_reminder(db_session, *, kind=ReminderKind.LESSON_STARTING, **lesson_overrides):
    club = await make_club(db_session, chat_id=CHAT_ID, reminders_topic_id=17)
    lesson = await make_lesson(
        db_session,
        club,
        **{
            "kind": LessonKind.CURATOR_CALL,
            "starts_at": CALL_OVER,
            "call_url": CALL_URL,
            "platform_lesson_id": 50002,
            **lesson_overrides,
        },
    )
    return await make_reminder(
        db_session,
        lesson,
        kind=kind,
        status=ReminderStatus.SENT,
        sent_at=lesson.starts_at,
        message_id=321,
    )


def _edit_error(error_class):
    method = EditMessageReplyMarkup(chat_id=CHAT_ID, message_id=321)
    return error_class(method=method, message="message to edit not found")


async def test_lists_reminders_of_calls_over_and_of_cancelled_lessons(service, db_session) -> None:
    call_over = await _sent_reminder(db_session)
    cancelled = await _sent_reminder(db_session, starts_at=DEFAULT_NOW + timedelta(days=1), is_cancelled=True)
    await _sent_reminder(db_session, starts_at=CALL_OVER + timedelta(minutes=1))
    await _sent_reminder(db_session, call_url=None)

    assert await service.list_outdated_ids() == [call_over.id, cancelled.id]


async def test_leaves_only_the_lesson_button_after_the_call(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session)

    await service.trim(reminder.id)

    kwargs = bot.edit_message_reply_markup.call_args.kwargs
    assert (kwargs["chat_id"], kwargs["message_id"]) == (CHAT_ID, 321)
    assert [(button.text, button.url) for button in kwargs["reply_markup"].inline_keyboard[0]] == [
        ("Открыть урок", LESSON_URL),
    ]
    assert (reminder.call_button_removed_at, reminder.buttons_removed_at) == (DEFAULT_NOW, None)
    assert await service.list_outdated_ids() == []


async def test_removes_all_buttons_when_the_lesson_is_cancelled(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, starts_at=DEFAULT_NOW + timedelta(days=1), is_cancelled=True)

    await service.trim(reminder.id)

    assert bot.edit_message_reply_markup.call_args.kwargs["reply_markup"] is None
    assert reminder.buttons_removed_at == DEFAULT_NOW
    assert await service.list_outdated_ids() == []


async def test_removes_the_lesson_button_left_after_the_call_on_cancel(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, is_cancelled=True)
    reminder.call_button_removed_at = DEFAULT_NOW - timedelta(days=1)

    await service.trim(reminder.id)

    assert bot.edit_message_reply_markup.call_args.kwargs["reply_markup"] is None
    assert reminder.call_button_removed_at == DEFAULT_NOW - timedelta(days=1)
    assert reminder.buttons_removed_at == DEFAULT_NOW


async def test_does_not_edit_a_reminder_that_had_no_call_button(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, kind=ReminderKind.HOMEWORK_DEADLINE)

    await service.trim(reminder.id)

    bot.edit_message_reply_markup.assert_not_called()
    assert reminder.call_button_removed_at == DEFAULT_NOW


async def test_gives_up_on_a_message_that_cannot_be_edited(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session)
    bot.edit_message_reply_markup.side_effect = _edit_error(TelegramBadRequest)

    await service.trim(reminder.id)

    assert reminder.call_button_removed_at == DEFAULT_NOW


async def test_retries_after_a_network_error(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session)
    bot.edit_message_reply_markup.side_effect = _edit_error(TelegramNetworkError)

    await service.trim(reminder.id)

    assert reminder.call_button_removed_at is None
    assert await service.list_outdated_ids() == [reminder.id]
