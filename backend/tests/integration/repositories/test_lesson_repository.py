from datetime import UTC, datetime

from app.repositories import LessonRepository
from tests.factories import make_club, make_lesson

START = datetime(2026, 10, 1, tzinfo=UTC)
END = datetime(2026, 11, 1, tzinfo=UTC)


async def test_schedule_has_lessons_starting_or_due_in_the_period(db_session) -> None:
    club = await make_club(db_session)
    other = await make_club(db_session)
    starting = await make_lesson(db_session, club, starts_at=datetime(2026, 10, 5, tzinfo=UTC))
    due = await make_lesson(
        db_session,
        club,
        starts_at=datetime(2026, 9, 28, tzinfo=UTC),
        homework_deadline_at=datetime(2026, 10, 2, tzinfo=UTC),
    )
    await make_lesson(db_session, club, starts_at=datetime(2026, 9, 20, tzinfo=UTC))
    await make_lesson(db_session, club, starts_at=END)
    await make_lesson(db_session, club, starts_at=datetime(2026, 10, 6, tzinfo=UTC), is_cancelled=True)
    await make_lesson(db_session, other, starts_at=datetime(2026, 10, 5, tzinfo=UTC))

    lessons = await LessonRepository(db_session).list_for_schedule(club_id=club.id, start=START, end=END)

    assert lessons == [due, starting]
