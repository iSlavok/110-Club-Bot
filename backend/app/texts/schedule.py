from datetime import date
from html import escape
from itertools import groupby

from app.enums import LessonKind
from app.schemas import ClubSchedule, ScheduleItem
from app.texts.reminders import MONTHS, WEEKDAYS
from app.utils import BUSINESS_TZ

NO_CLUBS = "Расписание видно участникам клуба. Проверь свой доступ: /status."
EMPTY = "До конца блока уроков и дедлайнов нет."
# Keeps several clubs within Telegram's 4096-character message limit.
MAX_ITEMS = 40
_SUBJECTS = {LessonKind.LESSON: "урок", LessonKind.CURATOR_CALL: "созвон с куратором"}
_HOMEWORK_TO = {LessonKind.LESSON: "к уроку", LessonKind.CURATOR_CALL: "к созвону"}


def schedule(schedules: list[ClubSchedule]) -> str:
    if not schedules:
        return NO_CLUBS
    return "\n\n".join(_club(club) for club in schedules)


def _club(club: ClubSchedule) -> str:
    lines = [f"<b>{escape(club.club_title)}</b>, {escape(club.block_title)}"]
    if not club.items:
        lines.append(EMPTY)
    shown = club.items[:MAX_ITEMS]
    for day, items in groupby(shown, key=lambda item: item.moment.astimezone(BUSINESS_TZ).date()):
        lines.append(f"\n{_day(day)}")
        lines.extend(_item(item) for item in items)
    hidden = len(club.items) - len(shown)
    if hidden > 0:
        lines.append(f"…и ещё {hidden}")
    return "\n".join(lines)


def _day(day: date) -> str:
    return f"{WEEKDAYS[day.weekday()].capitalize()}, {day.day} {MONTHS[day.month - 1]}"


def _item(item: ScheduleItem) -> str:
    clock = f"{item.moment.astimezone(BUSINESS_TZ):%H:%M}"
    title = escape(item.lesson_title)
    if item.is_homework_deadline:
        return f"• {clock} — дедлайн ДЗ {_HOMEWORK_TO[item.lesson_kind]} «{title}»"
    return f"• {clock} — {_SUBJECTS[item.lesson_kind]} «{title}»"
