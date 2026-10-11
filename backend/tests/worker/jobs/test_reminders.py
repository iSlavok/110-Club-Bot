from datetime import timedelta
from unittest.mock import MagicMock

from app.enums import ReminderStatus
from app.services import ReminderDispatchService
from tests.factories import make_club, make_lesson, make_reminder
from tests.providers import DEFAULT_NOW
from worker.jobs import dispatch_reminders


async def test_one_crashing_reminder_does_not_stop_the_others(container, request_container, db_session, bot) -> None:
    club = await make_club(db_session, chat_id=-100_1, reminders_topic_id=5)
    lesson = await make_lesson(db_session, club, starts_at=DEFAULT_NOW + timedelta(hours=1))
    first = await make_reminder(db_session, lesson, send_at=DEFAULT_NOW - timedelta(minutes=1))
    second = await make_reminder(db_session, lesson, send_at=DEFAULT_NOW)
    bot.send_message.side_effect = [RuntimeError("boom"), MagicMock(message_id=7)]
    service = await request_container.get(ReminderDispatchService)

    await dispatch_reminders(container=container, reminder_dispatch_service=service)

    assert (first.status, first.attempts, first.error) == (ReminderStatus.PENDING, 1, "RuntimeError('boom')")
    assert (second.status, second.message_id) == (ReminderStatus.SENT, 7)
