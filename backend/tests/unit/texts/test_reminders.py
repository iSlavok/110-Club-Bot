from datetime import UTC, datetime, timedelta

import pytest

from app import texts
from app.enums import LessonKind, ReminderKind, ReminderStatus
from app.schemas import LessonDraft, LessonDTO, ReminderButton, ReminderWithLessonDTO

# 12:00 in Moscow, Thursday.
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
CALL_URL = "https://meet.example.com/abc"
PLATFORM_LESSON_ID = 50002
CALL_BUTTON = ReminderButton(text="Подключиться", url=CALL_URL)
LESSON_BUTTON = ReminderButton(text="Открыть урок", url="https://lk.100points.ru/student/lesson/50002")


def _lesson(**overrides) -> LessonDTO:
    values = {
        "id": 1,
        "club_id": 1,
        "kind": LessonKind.LESSON,
        "title": "Кислоты",
        "description": None,
        "starts_at": datetime(2026, 10, 2, 16, 0, tzinfo=UTC),
        "call_url": None,
        "platform_lesson_id": None,
        "is_cancelled": False,
        "reminder_offsets": [],
        "homework_deadline_at": None,
        "homework_reminder_offsets": [],
        "created_at": NOW,
        "updated_at": NOW,
    }
    return LessonDTO.model_validate({**values, **overrides})


def _render(reminder_kind: ReminderKind, /, *, sent_at: datetime = NOW, **lesson) -> str:
    return texts.reminders.render(_reminder(reminder_kind, **lesson), sent_at)


def _reminder(reminder_kind: ReminderKind, /, **lesson) -> ReminderWithLessonDTO:
    return ReminderWithLessonDTO(
        id=1,
        club_id=1,
        lesson_id=1,
        kind=reminder_kind,
        text=None,
        send_at=NOW,
        status=ReminderStatus.PENDING,
        attempts=0,
        sent_at=None,
        message_id=None,
        error=None,
        buttons=None,
        buttons_checked_at=None,
        buttons_lesson_version=None,
        created_at=NOW,
        updated_at=NOW,
        lesson=_lesson(**lesson),
    )


def test_upcoming_lesson_tomorrow_with_description() -> None:
    text = _render(ReminderKind.LESSON_UPCOMING, call_url=CALL_URL, description="Повторить <оксиды>")

    assert text == "<b>Урок «Кислоты»</b>\nЗавтра в 19:00\n\nПовторить &lt;оксиды&gt;"


@pytest.mark.parametrize(
    ("starts_in", "expected"),
    [
        (timedelta(minutes=1), "Через 1 минуту, в 12:01"),
        (timedelta(minutes=45), "Через 45 минут, в 12:45"),
        (timedelta(minutes=60), "Через час, в 13:00"),
        (timedelta(minutes=90), "Через 1 ч 30 мин, в 13:30"),
        (timedelta(hours=3), "Сегодня в 15:00"),
        (timedelta(days=2), "Послезавтра в 12:00"),
        (timedelta(days=5), "6 октября (вт) в 12:00"),
    ],
)
def test_upcoming_lesson_time_phrases(starts_in, expected) -> None:
    text = _render(ReminderKind.LESSON_UPCOMING, starts_at=NOW + starts_in)

    assert text == f"<b>Урок «Кислоты»</b>\n{expected}"


@pytest.mark.parametrize(
    ("late_by", "expected"),
    [
        (timedelta(seconds=40), "Через час, в 13:00"),
        (timedelta(minutes=5), "Через час, в 13:00"),
        (timedelta(minutes=6), "Через 54 минуты, в 13:00"),
    ],
)
def test_relative_time_is_counted_from_send_at_unless_sent_much_later(late_by, expected) -> None:
    text = _render(ReminderKind.LESSON_UPCOMING, sent_at=NOW + late_by, starts_at=NOW + timedelta(hours=1))

    assert text == f"<b>Урок «Кислоты»</b>\n{expected}"


def test_curator_call_starting() -> None:
    text = _render(
        ReminderKind.LESSON_STARTING,
        kind=LessonKind.CURATOR_CALL,
        title="Разбор <ДЗ>",
        call_url=CALL_URL,
    )

    assert text == "<b>Созвон с куратором «Разбор &lt;ДЗ&gt;» начинается</b>"


def test_homework_deadline() -> None:
    text = _render(ReminderKind.HOMEWORK_DEADLINE, homework_deadline_at=datetime(2026, 10, 3, 20, 59, tzinfo=UTC))

    assert text == "<b>ДЗ к уроку «Кислоты»</b>\nДедлайн — послезавтра в 23:59"


def test_lesson_rescheduled() -> None:
    text = _render(ReminderKind.LESSON_RESCHEDULED)

    assert text == "<b>Урок «Кислоты» перенесён</b>\nНовое время: завтра в 19:00"


def test_lesson_cancelled() -> None:
    text = _render(ReminderKind.LESSON_CANCELLED, kind=LessonKind.CURATOR_CALL)

    assert text == "<b>Созвон с куратором «Кислоты» отменён</b>\nБыл запланирован на завтра в 19:00."


def test_homework_deadline_changed() -> None:
    text = _render(
        ReminderKind.HOMEWORK_DEADLINE_CHANGED,
        kind=LessonKind.CURATOR_CALL,
        homework_deadline_at=datetime(2026, 10, 2, 20, 0, tzinfo=UTC),
    )

    assert text == "<b>Дедлайн ДЗ к созвону «Кислоты» изменён</b>\nНовый дедлайн — завтра в 23:00"


def test_homework_removed() -> None:
    assert _render(ReminderKind.HOMEWORK_REMOVED) == "<b>ДЗ к уроку «Кислоты» отменено</b>\nСдавать его не нужно."


@pytest.mark.parametrize(
    "kind",
    [ReminderKind.LESSON_UPCOMING, ReminderKind.LESSON_STARTING, ReminderKind.LESSON_RESCHEDULED],
)
def test_lesson_reminders_get_the_call_and_the_platform_lesson_buttons(kind) -> None:
    reminder = _reminder(kind, call_url=CALL_URL, platform_lesson_id=PLATFORM_LESSON_ID)

    assert texts.reminders.buttons(reminder) == [CALL_BUTTON, LESSON_BUTTON]


@pytest.mark.parametrize(
    ("call_url", "platform_lesson_id", "expected"),
    [
        (CALL_URL, None, [CALL_BUTTON]),
        (None, PLATFORM_LESSON_ID, [LESSON_BUTTON]),
        (None, None, []),
    ],
)
def test_each_button_needs_only_its_own_link(call_url, platform_lesson_id, expected) -> None:
    reminder = _reminder(ReminderKind.LESSON_UPCOMING, call_url=call_url, platform_lesson_id=platform_lesson_id)

    assert texts.reminders.buttons(reminder) == expected


@pytest.mark.parametrize("kind", [ReminderKind.HOMEWORK_DEADLINE, ReminderKind.HOMEWORK_DEADLINE_CHANGED])
def test_homework_reminders_open_the_lesson_without_the_call(kind) -> None:
    reminder = _reminder(kind, call_url=CALL_URL, platform_lesson_id=PLATFORM_LESSON_ID, homework_deadline_at=NOW)

    assert texts.reminders.buttons(reminder) == [LESSON_BUTTON]


@pytest.mark.parametrize("kind", [ReminderKind.LESSON_CANCELLED, ReminderKind.HOMEWORK_REMOVED])
def test_cancellations_have_no_buttons(kind) -> None:
    reminder = _reminder(kind, call_url=CALL_URL, platform_lesson_id=PLATFORM_LESSON_ID)

    assert texts.reminders.buttons(reminder) == []


def test_deadline_reminder_without_homework_is_a_bug() -> None:
    with pytest.raises(ValueError, match="no homework"):
        _render(ReminderKind.HOMEWORK_DEADLINE)


def test_renders_a_draft_lesson() -> None:
    draft = LessonDraft(kind=LessonKind.LESSON, title="Кислоты", starts_at=NOW + timedelta(minutes=30))

    text = texts.reminders.render_message(ReminderKind.LESSON_UPCOMING, draft, NOW)

    assert text == "<b>Урок «Кислоты»</b>\nЧерез 30 минут, в 12:30"


def test_draft_lesson_gets_buttons_before_it_is_saved() -> None:
    draft = LessonDraft(
        kind=LessonKind.LESSON,
        title="Кислоты",
        starts_at=NOW,
        call_url=CALL_URL,
        platform_lesson_id=PLATFORM_LESSON_ID,
    )

    assert texts.reminders.lesson_buttons(ReminderKind.LESSON_STARTING, draft) == [CALL_BUTTON, LESSON_BUTTON]


def _message(text: str) -> ReminderWithLessonDTO:
    return ReminderWithLessonDTO(
        id=1,
        club_id=1,
        lesson_id=None,
        kind=ReminderKind.MESSAGE,
        text=text,
        send_at=NOW,
        status=ReminderStatus.PENDING,
        attempts=0,
        sent_at=None,
        message_id=None,
        error=None,
        buttons=None,
        buttons_checked_at=None,
        buttons_lesson_version=None,
        created_at=NOW,
        updated_at=NOW,
        lesson=None,
    )


def test_message_goes_out_as_written() -> None:
    text = '<b>Привет!!</b>\nЗапись уже на платформе: <a href="https://lk.example/1">урок</a>'

    assert texts.reminders.render(_message(text), NOW + timedelta(hours=3)) == text


def test_message_has_no_buttons() -> None:
    assert texts.reminders.buttons(_message("Привет")) == []


def test_subject_of_a_message_is_its_start_as_plain_text() -> None:
    message = _message("<b>Привет!!</b>\nЗапись созвона &amp; ДЗ уже на платформе, дедлайн в пятницу")

    assert texts.reminders.subject(message) == "«Привет!! Запись созвона &amp; ДЗ уже на плат…»"


def test_subject_of_a_lesson_reminder_is_its_title() -> None:
    reminder = _message("x").model_copy(update={"lesson": _lesson(title="Кислоты <1>"), "text": None})

    assert texts.reminders.subject(reminder) == "«Кислоты &lt;1&gt;»"
