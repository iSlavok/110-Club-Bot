from sqlalchemy import select

from app.enums import ReminderStatus
from app.models import Reminder
from tests.factories import make_club, make_lesson, make_reminder


async def test_new_reminder_is_pending_with_no_attempts(db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)

    reminder = await make_reminder(db_session, lesson)

    assert reminder.status is ReminderStatus.PENDING
    assert reminder.attempts == 0


async def test_reminders_are_deleted_with_their_lesson(db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)
    await make_reminder(db_session, lesson)

    await db_session.delete(lesson)
    await db_session.flush()

    statement = select(Reminder).where(Reminder.lesson_id == lesson.id)
    remaining = await db_session.scalars(statement)
    assert list(remaining) == []
