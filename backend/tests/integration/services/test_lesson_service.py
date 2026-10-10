from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.enums import LessonKind, LessonView, ReminderKind, ReminderStatus
from app.exceptions import ClubNotFoundError, EmptyUpdateError, LessonCancelledError, LessonNotFoundError
from app.models import Reminder
from app.schemas import LessonCreate, LessonUpdate, PageParams
from app.services import LessonService
from tests.factories import make_club, make_lesson, make_reminder, set_app_settings
from tests.providers import DEFAULT_NOW

STARTS_AT = datetime(2026, 10, 3, 16, 0, tzinfo=UTC)
DEADLINE = datetime(2026, 10, 6, 20, 59, tzinfo=UTC)


@pytest.fixture
async def service(request_container) -> LessonService:
    return await request_container.get(LessonService)


async def _reminders(db_session, lesson_id: int) -> list[tuple[ReminderKind, datetime, ReminderStatus]]:
    statement = select(Reminder).where(Reminder.lesson_id == lesson_id).order_by(Reminder.send_at, Reminder.id)
    reminders = await db_session.scalars(statement)
    return [(reminder.kind, reminder.send_at, reminder.status) for reminder in reminders]


def _create(**overrides) -> LessonCreate:
    return LessonCreate.model_validate(
        {"kind": "lesson", "title": "Кислоты", "starts_at": STARTS_AT.isoformat(), **overrides},
    )


async def test_create_plans_lesson_reminders_from_settings_defaults(service, db_session) -> None:
    club = await make_club(db_session)

    lesson = await service.create(club.id, _create())

    assert lesson.reminder_offsets == [1440, 60, 0]
    assert lesson.homework_reminder_offsets == [2880, 1440, 180]
    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.LESSON_UPCOMING, STARTS_AT - timedelta(days=1), ReminderStatus.PENDING),
        (ReminderKind.LESSON_UPCOMING, STARTS_AT - timedelta(hours=1), ReminderStatus.PENDING),
        (ReminderKind.LESSON_STARTING, STARTS_AT, ReminderStatus.PENDING),
    ]


async def test_create_uses_changed_settings_defaults(service, db_session) -> None:
    club = await make_club(db_session)
    await set_app_settings(db_session, default_lesson_offsets=[30])

    lesson = await service.create(club.id, _create())

    assert lesson.reminder_offsets == [30]


async def test_create_skips_offsets_already_in_the_past(service, db_session) -> None:
    club = await make_club(db_session)
    starts_at = DEFAULT_NOW + timedelta(minutes=90)

    lesson = await service.create(club.id, _create(starts_at=starts_at.isoformat(), reminder_offsets=[1440, 60, 0]))

    assert [kind for kind, _, _ in await _reminders(db_session, lesson.id)] == [
        ReminderKind.LESSON_UPCOMING,
        ReminderKind.LESSON_STARTING,
    ]


async def test_now_offset_is_sent_on_the_next_tick(service, db_session) -> None:
    club = await make_club(db_session)
    starts_at = DEFAULT_NOW + timedelta(minutes=90, seconds=30)

    lesson = await service.create(club.id, _create(starts_at=starts_at.isoformat(), reminder_offsets=[90]))

    [(kind, send_at, _)] = await _reminders(db_session, lesson.id)
    assert kind is ReminderKind.LESSON_UPCOMING
    assert DEFAULT_NOW < send_at < DEFAULT_NOW + timedelta(minutes=1)


async def test_create_plans_homework_deadline_reminders(service, db_session) -> None:
    club = await make_club(db_session)

    lesson = await service.create(
        club.id,
        _create(reminder_offsets=[], homework_deadline_at=DEADLINE.isoformat(), homework_reminder_offsets=[1440, 180]),
    )

    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.HOMEWORK_DEADLINE, DEADLINE - timedelta(days=1), ReminderStatus.PENDING),
        (ReminderKind.HOMEWORK_DEADLINE, DEADLINE - timedelta(hours=3), ReminderStatus.PENDING),
    ]


async def test_create_in_unknown_club_fails(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.create(999_999, _create())


async def test_reschedule_replans_pending_and_keeps_sent(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=STARTS_AT, reminder_offsets=[1440, 60])
    await make_reminder(db_session, lesson, send_at=DEFAULT_NOW - timedelta(hours=1), status=ReminderStatus.SENT)
    await make_reminder(db_session, lesson, send_at=STARTS_AT - timedelta(hours=1))
    new_start = STARTS_AT + timedelta(days=1)

    await service.update(lesson.id, LessonUpdate.model_validate({"starts_at": new_start.isoformat()}))

    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.LESSON_UPCOMING, DEFAULT_NOW - timedelta(hours=1), ReminderStatus.SENT),
        (ReminderKind.LESSON_UPCOMING, STARTS_AT - timedelta(hours=1), ReminderStatus.CANCELLED),
        (ReminderKind.LESSON_UPCOMING, new_start - timedelta(days=1), ReminderStatus.PENDING),
        (ReminderKind.LESSON_UPCOMING, new_start - timedelta(hours=1), ReminderStatus.PENDING),
    ]


async def test_reschedule_with_notify_chat_sends_a_notice_now(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=STARTS_AT)
    new_start = STARTS_AT + timedelta(hours=2)

    await service.update(
        lesson.id,
        LessonUpdate.model_validate({"starts_at": new_start.isoformat()}),
        notify_chat=True,
    )

    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.LESSON_RESCHEDULED, DEFAULT_NOW, ReminderStatus.PENDING),
    ]


async def test_title_change_neither_replans_nor_notifies(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=STARTS_AT, reminder_offsets=[60])
    await make_reminder(db_session, lesson, send_at=STARTS_AT - timedelta(hours=1))

    updated = await service.update(lesson.id, LessonUpdate.model_validate({"title": "Основания"}), notify_chat=True)

    assert updated.title == "Основания"
    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.LESSON_UPCOMING, STARTS_AT - timedelta(hours=1), ReminderStatus.PENDING),
    ]


async def test_offsets_change_replans_without_notice(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=STARTS_AT, reminder_offsets=[60])
    await make_reminder(db_session, lesson, send_at=STARTS_AT - timedelta(hours=1))

    await service.update(lesson.id, LessonUpdate.model_validate({"reminder_offsets": [0]}), notify_chat=True)

    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.LESSON_UPCOMING, STARTS_AT - timedelta(hours=1), ReminderStatus.CANCELLED),
        (ReminderKind.LESSON_STARTING, STARTS_AT, ReminderStatus.PENDING),
    ]


async def test_adding_homework_plans_reminders_without_notice(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=STARTS_AT, homework_reminder_offsets=[180])

    await service.update(
        lesson.id,
        LessonUpdate.model_validate({"homework_deadline_at": DEADLINE.isoformat()}),
        notify_chat=True,
    )

    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.HOMEWORK_DEADLINE, DEADLINE - timedelta(hours=3), ReminderStatus.PENDING),
    ]


async def test_moving_the_deadline_replans_and_notifies_when_asked(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(
        db_session,
        club,
        starts_at=STARTS_AT,
        reminder_offsets=[60],
        homework_deadline_at=DEADLINE,
        homework_reminder_offsets=[180],
    )
    lesson_reminder = await make_reminder(db_session, lesson, send_at=STARTS_AT - timedelta(hours=1))
    await make_reminder(
        db_session,
        lesson,
        kind=ReminderKind.HOMEWORK_DEADLINE,
        send_at=DEADLINE - timedelta(hours=3),
    )
    new_deadline = DEADLINE + timedelta(days=1)

    await service.update(
        lesson.id,
        LessonUpdate.model_validate({"homework_deadline_at": new_deadline.isoformat()}),
        notify_chat=True,
    )

    assert lesson_reminder.status is ReminderStatus.PENDING
    assert await _reminders(db_session, lesson.id) == [
        (ReminderKind.HOMEWORK_DEADLINE_CHANGED, DEFAULT_NOW, ReminderStatus.PENDING),
        (ReminderKind.LESSON_UPCOMING, STARTS_AT - timedelta(hours=1), ReminderStatus.PENDING),
        (ReminderKind.HOMEWORK_DEADLINE, DEADLINE - timedelta(hours=3), ReminderStatus.CANCELLED),
        (ReminderKind.HOMEWORK_DEADLINE, new_deadline - timedelta(hours=3), ReminderStatus.PENDING),
    ]


@pytest.mark.parametrize(("notify_chat", "notices"), [(True, [ReminderKind.HOMEWORK_REMOVED]), (False, [])])
async def test_removing_homework_cancels_its_reminders(service, db_session, notify_chat, notices) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, homework_deadline_at=DEADLINE, homework_reminder_offsets=[180])
    await make_reminder(db_session, lesson, kind=ReminderKind.HOMEWORK_DEADLINE, send_at=DEADLINE - timedelta(hours=3))

    updated = await service.update(
        lesson.id,
        LessonUpdate.model_validate({"homework_deadline_at": None}),
        notify_chat=notify_chat,
    )

    assert updated.homework_deadline_at is None
    reminders = await _reminders(db_session, lesson.id)
    assert (ReminderKind.HOMEWORK_DEADLINE, DEADLINE - timedelta(hours=3), ReminderStatus.CANCELLED) in reminders
    assert [kind for kind, _, status in reminders if status is ReminderStatus.PENDING] == notices


async def test_empty_patch_is_rejected(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)

    with pytest.raises(EmptyUpdateError):
        await service.update(lesson.id, LessonUpdate.model_validate({}))


async def test_unknown_lesson_is_not_found(service) -> None:
    with pytest.raises(LessonNotFoundError):
        await service.get(999_999)


@pytest.mark.parametrize("notify_chat", [True, False])
async def test_cancel_cancels_every_pending_reminder(service, db_session, notify_chat) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, starts_at=STARTS_AT)
    await make_reminder(db_session, lesson, send_at=STARTS_AT - timedelta(hours=1))
    await make_reminder(db_session, lesson, kind=ReminderKind.HOMEWORK_DEADLINE, send_at=DEADLINE)
    await make_reminder(db_session, lesson, send_at=DEFAULT_NOW - timedelta(hours=1), status=ReminderStatus.SENT)

    cancelled = await service.cancel(lesson.id, notify_chat=notify_chat)

    assert cancelled.is_cancelled
    statuses = [(kind, status) for kind, _, status in await _reminders(db_session, lesson.id)]
    expected_notice = [(ReminderKind.LESSON_CANCELLED, ReminderStatus.PENDING)] if notify_chat else []
    assert statuses == [
        (ReminderKind.LESSON_UPCOMING, ReminderStatus.SENT),
        *expected_notice,
        (ReminderKind.LESSON_UPCOMING, ReminderStatus.CANCELLED),
        (ReminderKind.HOMEWORK_DEADLINE, ReminderStatus.CANCELLED),
    ]


async def test_cancelled_lesson_cannot_be_changed_or_cancelled_again(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, is_cancelled=True)

    with pytest.raises(LessonCancelledError):
        await service.update(lesson.id, LessonUpdate.model_validate({"title": "Новое"}))
    with pytest.raises(LessonCancelledError):
        await service.cancel(lesson.id)


async def _titles(service, club_id: int, view: LessonView, *, include_cancelled: bool = False) -> list[str]:
    page = await service.list_page(club_id, PageParams(), view=view, include_cancelled=include_cancelled)
    return [lesson.title for lesson in page.items]


async def test_feed_views_and_order(service, db_session) -> None:
    club = await make_club(db_session)
    other_club = await make_club(db_session)
    for title, shift in (("past-2", -48), ("past-1", -1), ("next-1", 1), ("next-2", 48)):
        await make_lesson(db_session, club, title=title, starts_at=DEFAULT_NOW + timedelta(hours=shift))
    await make_lesson(db_session, other_club, title="other", starts_at=DEFAULT_NOW + timedelta(hours=2))

    assert await _titles(service, club.id, LessonView.UPCOMING) == ["next-1", "next-2"]
    assert await _titles(service, club.id, LessonView.PAST) == ["past-1", "past-2"]
    assert await _titles(service, club.id, LessonView.ALL) == ["next-2", "next-1", "past-1", "past-2"]


async def test_feed_shows_cancelled_only_when_asked(service, db_session) -> None:
    club = await make_club(db_session)
    await make_lesson(db_session, club, title="active", starts_at=DEFAULT_NOW + timedelta(hours=1))
    await make_lesson(
        db_session, club, title="cancelled", starts_at=DEFAULT_NOW + timedelta(hours=2), is_cancelled=True
    )

    assert await _titles(service, club.id, LessonView.UPCOMING) == ["active"]
    assert await _titles(service, club.id, LessonView.UPCOMING, include_cancelled=True) == ["active", "cancelled"]


async def test_feed_of_unknown_club_fails(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.list_page(999_999, PageParams(), view=LessonView.ALL, include_cancelled=False)


async def test_get_returns_lesson_fields(service, db_session) -> None:
    club = await make_club(db_session)
    lesson = await make_lesson(db_session, club, kind=LessonKind.CURATOR_CALL, call_url="https://meet.example.com/x")

    found = await service.get(lesson.id)

    assert (found.kind, found.call_url, found.club_id) == (
        LessonKind.CURATOR_CALL,
        "https://meet.example.com/x",
        club.id,
    )
