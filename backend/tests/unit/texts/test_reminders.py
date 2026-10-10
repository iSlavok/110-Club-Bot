from datetime import UTC, datetime, timedelta

import pytest

from app import texts
from app.enums import LessonKind, ReminderKind, ReminderStatus
from app.schemas import LessonDTO, ReminderWithLessonDTO

# 12:00 in Moscow, Thursday.
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def _lesson(**overrides) -> LessonDTO:
    values = {
        "id": 1,
        "club_id": 1,
        "kind": LessonKind.LESSON,
        "title": "Кислоты",
        "description": None,
        "starts_at": datetime(2026, 10, 2, 16, 0, tzinfo=UTC),
        "call_url": None,
        "is_cancelled": False,
        "reminder_offsets": [],
        "homework_deadline_at": None,
        "homework_reminder_offsets": [],
        "created_at": NOW,
        "updated_at": NOW,
    }
    return LessonDTO.model_validate({**values, **overrides})


def _render(reminder_kind: ReminderKind, /, **lesson) -> str:
    reminder = ReminderWithLessonDTO(
        id=1,
        club_id=1,
        lesson_id=1,
        kind=reminder_kind,
        send_at=NOW,
        status=ReminderStatus.PENDING,
        attempts=0,
        sent_at=None,
        message_id=None,
        error=None,
        created_at=NOW,
        updated_at=NOW,
        lesson=_lesson(**lesson),
    )
    return texts.reminders.render(reminder, NOW)


def test_upcoming_lesson_tomorrow_with_link_and_description() -> None:
    text = _render(
        ReminderKind.LESSON_UPCOMING,
        call_url="https://meet.example.com/abc?x=1&y=2",
        description="Повторить <оксиды>",
    )

    assert text == (
        "<b>Урок «Кислоты»</b>\n"
        "Завтра в 19:00 (МСК)\n"
        'Подключиться: <a href="https://meet.example.com/abc?x=1&amp;y=2">ссылка на созвон</a>\n'
        "\nПовторить &lt;оксиды&gt;"
    )


@pytest.mark.parametrize(
    ("starts_in", "expected"),
    [
        (timedelta(minutes=1), "Через 1 минуту, в 12:01 (МСК)"),
        (timedelta(minutes=45), "Через 45 минут, в 12:45 (МСК)"),
        (timedelta(minutes=60), "Через час, в 13:00 (МСК)"),
        (timedelta(minutes=90), "Через 1 ч 30 мин, в 13:30 (МСК)"),
        (timedelta(hours=3), "Сегодня в 15:00 (МСК)"),
        (timedelta(days=2), "Послезавтра в 12:00 (МСК)"),
        (timedelta(days=5), "6 октября (вт) в 12:00 (МСК)"),
    ],
)
def test_upcoming_lesson_time_phrases(starts_in, expected) -> None:
    text = _render(ReminderKind.LESSON_UPCOMING, starts_at=NOW + starts_in)

    assert text == f"<b>Урок «Кислоты»</b>\n{expected}"


def test_curator_call_starting() -> None:
    text = _render(
        ReminderKind.LESSON_STARTING,
        kind=LessonKind.CURATOR_CALL,
        title="Разбор <ДЗ>",
        call_url="https://meet.example.com/abc",
    )

    assert text == (
        "<b>Созвон с куратором «Разбор &lt;ДЗ&gt;» начинается</b>\n"
        'Подключиться: <a href="https://meet.example.com/abc">ссылка на созвон</a>'
    )


def test_homework_deadline() -> None:
    text = _render(ReminderKind.HOMEWORK_DEADLINE, homework_deadline_at=datetime(2026, 10, 3, 20, 59, tzinfo=UTC))

    assert text == "<b>Дедлайн ДЗ к уроку «Кислоты»</b>\nСдать до: послезавтра в 23:59 (МСК)"


def test_lesson_rescheduled() -> None:
    text = _render(ReminderKind.LESSON_RESCHEDULED)

    assert text == "<b>Урок «Кислоты» перенесён</b>\nНовое время: завтра в 19:00 (МСК)"


def test_lesson_cancelled() -> None:
    text = _render(ReminderKind.LESSON_CANCELLED, kind=LessonKind.CURATOR_CALL)

    assert text == "<b>Созвон с куратором «Кислоты» отменён</b>\nБыл запланирован на завтра в 19:00 (МСК)."


def test_homework_deadline_changed() -> None:
    text = _render(
        ReminderKind.HOMEWORK_DEADLINE_CHANGED,
        kind=LessonKind.CURATOR_CALL,
        homework_deadline_at=datetime(2026, 10, 2, 20, 0, tzinfo=UTC),
    )

    assert text == "<b>Дедлайн ДЗ к созвону «Кислоты» изменён</b>\nНовый дедлайн: завтра в 23:00 (МСК)"


def test_homework_removed() -> None:
    assert _render(ReminderKind.HOMEWORK_REMOVED) == "<b>ДЗ к уроку «Кислоты» отменено</b>\nСдавать его не нужно."


def test_deadline_reminder_without_homework_is_a_bug() -> None:
    with pytest.raises(ValueError, match="no homework"):
        _render(ReminderKind.HOMEWORK_DEADLINE)
