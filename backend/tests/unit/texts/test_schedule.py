from datetime import UTC, datetime, timedelta

from app import texts
from app.enums import LessonKind
from app.schemas import ClubSchedule, ScheduleItem

# Monday, 12 October, 19:00 in Moscow.
MOMENT = datetime(2026, 10, 12, 16, 0, tzinfo=UTC)


def _item(
    moment: datetime, title: str, *, kind: LessonKind = LessonKind.LESSON, deadline: bool = False
) -> ScheduleItem:
    return ScheduleItem(moment=moment, lesson_kind=kind, lesson_title=title, is_homework_deadline=deadline)


def test_items_are_grouped_by_moscow_day() -> None:
    schedule = ClubSchedule(
        club_title="Химия & <био>",
        block_title="Блок 5",
        items=[
            _item(MOMENT, "Кислоты <1>"),
            _item(MOMENT.replace(hour=20, minute=59), "Оксиды", deadline=True),
            _item(MOMENT + timedelta(days=2), "Разбор", kind=LessonKind.CURATOR_CALL),
            _item(MOMENT + timedelta(days=2, hours=1), "Разбор", kind=LessonKind.CURATOR_CALL, deadline=True),
        ],
    )

    assert texts.schedule.schedule([schedule]) == (
        "<b>Химия &amp; &lt;био&gt;</b>, Блок 5\n"
        "\nПн, 12 октября\n"
        "• 19:00 — урок «Кислоты &lt;1&gt;»\n"
        "• 23:59 — дедлайн ДЗ к уроку «Оксиды»\n"
        "\nСр, 14 октября\n"
        "• 19:00 — созвон с куратором «Разбор»\n"
        "• 20:00 — дедлайн ДЗ к созвону «Разбор»"
    )


def test_empty_club_and_no_clubs() -> None:
    empty = ClubSchedule(club_title="Химия", block_title="Блок 5", items=[])

    assert texts.schedule.schedule([empty]) == f"<b>Химия</b>, Блок 5\n{texts.schedule.EMPTY}"
    assert texts.schedule.schedule([]) == texts.schedule.NO_CLUBS


def test_long_schedule_is_cut() -> None:
    items = [_item(MOMENT + timedelta(hours=n), f"Урок {n}") for n in range(texts.schedule.MAX_ITEMS + 3)]

    text = texts.schedule.schedule([ClubSchedule(club_title="Химия", block_title="Блок 5", items=items)])

    assert text.count("• ") == texts.schedule.MAX_ITEMS
    assert text.endswith("…и ещё 3")
