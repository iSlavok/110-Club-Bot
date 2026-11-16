from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import EditMessageReplyMarkup

from app.enums import LessonKind, ReminderKind, ReminderStatus
from app.models import Club, Lesson
from app.services import ReminderButtonsService
from tests.factories import make_club, make_lesson, make_message, make_reminder
from tests.providers import DEFAULT_NOW

CHAT_ID = -100_555
CALL_URL = "https://meet.example.com/abc"
LESSON_URL = "https://lk.100points.ru/student/lesson/50002"
CALL = {"text": "Подключиться", "url": CALL_URL}
LESSON = {"text": "Открыть урок", "url": LESSON_URL}
CALL_OVER = DEFAULT_NOW - timedelta(hours=3)
SOON = DEFAULT_NOW + timedelta(hours=1)
CHECKED_AT = DEFAULT_NOW - timedelta(days=1)


@pytest.fixture
async def service(request_container) -> ReminderButtonsService:
    return await request_container.get(ReminderButtonsService)


async def _sent_reminder(
    db_session,
    *,
    kind=ReminderKind.LESSON_STARTING,
    buttons=None,
    checked_at=None,
    **lesson_overrides,
):
    club = await make_club(db_session, chat_id=CHAT_ID, reminders_topic_id=17)
    lesson = await make_lesson(
        db_session,
        club,
        **{
            "kind": LessonKind.CURATOR_CALL,
            "starts_at": SOON,
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
        sent_at=DEFAULT_NOW - timedelta(days=1),
        message_id=321,
        buttons=buttons,
        buttons_checked_at=checked_at,
        buttons_lesson_version=None if checked_at is None else lesson.updated_at,
    )


# Inside the test transaction now() never moves, so an edit of the lesson moves updated_at by hand.
async def _edit_lesson(db_session, reminder, **changes) -> None:
    lesson = await db_session.get(Lesson, reminder.lesson_id)
    for name, value in changes.items():
        setattr(lesson, name, value)
    lesson.updated_at += timedelta(seconds=1)
    await db_session.flush()


def _edited_buttons(bot) -> list[dict[str, str]] | None:
    kwargs = bot.edit_message_reply_markup.call_args.kwargs
    assert (kwargs["chat_id"], kwargs["message_id"]) == (CHAT_ID, 321)
    keyboard = kwargs["reply_markup"]
    if keyboard is None:
        return None
    return [{"text": button.text, "url": button.url} for button in keyboard.inline_keyboard[0]]


def _edit_error(error_class, message="message to edit not found"):
    method = EditMessageReplyMarkup(chat_id=CHAT_ID, message_id=321)
    return error_class(method=method, message=message)


async def test_lists_unchecked_changed_and_call_ended_reminders_newest_first(service, db_session) -> None:
    unchecked = await _sent_reminder(db_session, buttons=[CALL, LESSON])
    changed = await _sent_reminder(db_session, checked_at=CHECKED_AT)
    await _edit_lesson(db_session, changed, call_url="https://meet.example.com/new")
    call_ended = await _sent_reminder(db_session, starts_at=CALL_OVER, checked_at=CHECKED_AT)
    await _sent_reminder(db_session, checked_at=CHECKED_AT)
    await _sent_reminder(db_session, starts_at=CALL_OVER, checked_at=DEFAULT_NOW)
    await _sent_reminder(db_session, starts_at=CALL_OVER, call_url=None, checked_at=CHECKED_AT)
    pending = await _sent_reminder(db_session)
    pending.status = ReminderStatus.PENDING
    club = await db_session.get(Club, unchecked.club_id)
    await make_message(db_session, club, status=ReminderStatus.SENT, message_id=5)
    await db_session.flush()

    assert await service.list_stale_ids() == [call_ended.id, changed.id, unchecked.id]


async def test_marks_matching_buttons_checked_without_an_edit(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON])

    await service.sync(reminder.id)

    bot.edit_message_reply_markup.assert_not_called()
    assert reminder.buttons_checked_at == DEFAULT_NOW
    assert await service.list_stale_ids() == []


async def test_adds_the_call_link_set_after_the_reminder_was_sent(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[LESSON], call_url=None, checked_at=CHECKED_AT)
    await _edit_lesson(db_session, reminder, call_url=CALL_URL)

    await service.sync(reminder.id)

    assert _edited_buttons(bot) == [CALL, LESSON]
    assert reminder.buttons == [CALL, LESSON]
    assert await service.list_stale_ids() == []


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        (
            {"call_url": "https://meet.example.com/new"},
            [{"text": "Подключиться", "url": "https://meet.example.com/new"}, LESSON],
        ),
        ({"call_url": None}, [LESSON]),
        (
            {"platform_lesson_id": 50001},
            [CALL, {"text": "Открыть урок", "url": "https://lk.100points.ru/student/lesson/50001"}],
        ),
        ({"platform_lesson_id": None}, [CALL]),
    ],
)
async def test_buttons_follow_the_lesson_links(service, db_session, bot, changes, expected) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON], checked_at=CHECKED_AT)
    await _edit_lesson(db_session, reminder, **changes)

    await service.sync(reminder.id)

    assert _edited_buttons(bot) == expected
    assert reminder.buttons == expected


async def test_does_not_edit_when_the_lesson_changed_elsewhere(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON], checked_at=CHECKED_AT)
    await _edit_lesson(db_session, reminder, title="Другое название")

    await service.sync(reminder.id)

    bot.edit_message_reply_markup.assert_not_called()
    assert await service.list_stale_ids() == []


async def test_leaves_only_the_lesson_button_after_the_call(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON], starts_at=CALL_OVER, checked_at=CHECKED_AT)

    await service.sync(reminder.id)

    assert _edited_buttons(bot) == [LESSON]
    assert await service.list_stale_ids() == []


async def test_does_not_add_a_call_link_set_after_the_call(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[LESSON], starts_at=CALL_OVER)

    await service.sync(reminder.id)

    bot.edit_message_reply_markup.assert_not_called()


async def test_removes_all_buttons_when_the_lesson_is_cancelled(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON], checked_at=CHECKED_AT)
    await _edit_lesson(db_session, reminder, is_cancelled=True)

    await service.sync(reminder.id)

    assert _edited_buttons(bot) is None
    assert reminder.buttons == []


async def test_edits_a_reminder_sent_before_the_buttons_were_stored(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, starts_at=CALL_OVER)
    bot.edit_message_reply_markup.side_effect = _edit_error(TelegramBadRequest, "message is not modified")

    await service.sync(reminder.id)

    assert _edited_buttons(bot) == [LESSON]
    assert (reminder.buttons, reminder.buttons_checked_at) == ([LESSON], DEFAULT_NOW)


async def test_gives_up_on_a_message_that_cannot_be_edited(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON], starts_at=CALL_OVER)
    bot.edit_message_reply_markup.side_effect = _edit_error(TelegramBadRequest)

    await service.sync(reminder.id)

    assert reminder.buttons_checked_at == DEFAULT_NOW
    assert await service.list_stale_ids() == []


async def test_retries_after_a_network_error(service, db_session, bot) -> None:
    reminder = await _sent_reminder(db_session, buttons=[CALL, LESSON], starts_at=CALL_OVER)
    bot.edit_message_reply_markup.side_effect = _edit_error(TelegramNetworkError)

    await service.sync(reminder.id)

    assert (reminder.buttons, reminder.buttons_checked_at) == ([CALL, LESSON], None)
    assert await service.list_stale_ids() == [reminder.id]
