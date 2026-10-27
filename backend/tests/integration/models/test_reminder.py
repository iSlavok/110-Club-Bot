import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.enums import ReminderKind, ReminderStatus
from app.models import Reminder
from tests.factories import make_club, make_lesson, make_message, make_reminder


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


async def test_message_has_a_text_and_no_lesson(db_session) -> None:
    club = await make_club(db_session)

    message = await make_message(db_session, club)

    assert (message.lesson_id, message.kind) == (None, ReminderKind.MESSAGE)


@pytest.mark.parametrize(
    "broken",
    [
        {"text": None},
        {"kind": ReminderKind.LESSON_UPCOMING},
    ],
    ids=["message-without-text", "lesson-reminder-without-lesson"],
)
async def test_message_shape_is_enforced(db_session, broken) -> None:
    club = await make_club(db_session)

    with pytest.raises(IntegrityError):
        await make_message(db_session, club, **broken)


async def test_lesson_reminder_cannot_carry_a_text(db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)

    with pytest.raises(IntegrityError):
        await make_reminder(db_session, lesson, text="x")
