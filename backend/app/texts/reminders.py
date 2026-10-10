from collections.abc import Callable
from datetime import datetime
from html import escape

from app.enums import LessonKind, ReminderKind
from app.schemas import LessonDTO, ReminderWithLessonDTO
from app.utils import BUSINESS_TZ

_MONTHS = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)
_WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
_SUBJECTS = {LessonKind.LESSON: "Урок", LessonKind.CURATOR_CALL: "Созвон с куратором"}
_HOMEWORK_TO = {LessonKind.LESSON: "к уроку", LessonKind.CURATOR_CALL: "к созвону"}
# Closer than this, "через 45 минут" reads better than a clock time.
_RELATIVE_MINUTES = 120
_MINUTES_IN_HOUR = 60
# Russian plural forms: 1 минуту, 2-4 минуты, 5-20 минут; 11-14 always take the "many" form.
_ELEVEN = 11
_FEW_ENDINGS = frozenset({2, 3, 4})
_FEW_EXCEPTIONS = frozenset({12, 13, 14})


def render(reminder: ReminderWithLessonDTO, now: datetime) -> str:
    return _RENDERERS[reminder.kind](reminder.lesson, now)


# now is the moment the message goes out: relative times ("через час") are counted from it.
def _lesson_upcoming(lesson: LessonDTO, now: datetime) -> str:
    return _join(
        f"<b>{_name(lesson)}</b>",
        _capitalize(_when(lesson.starts_at, now)),
        _call_link(lesson),
        _description(lesson),
    )


def _lesson_starting(lesson: LessonDTO, _now: datetime) -> str:
    return _join(f"<b>{_name(lesson)} начинается</b>", _call_link(lesson), _description(lesson))


def _homework_deadline(lesson: LessonDTO, now: datetime) -> str:
    return _join(f"<b>Дедлайн {_homework(lesson)}</b>", f"Сдать до: {_when(_deadline(lesson), now)}")


def _lesson_rescheduled(lesson: LessonDTO, now: datetime) -> str:
    return _join(
        f"<b>{_name(lesson)} перенесён</b>",
        f"Новое время: {_when(lesson.starts_at, now)}",
        _call_link(lesson),
    )


def _lesson_cancelled(lesson: LessonDTO, now: datetime) -> str:
    return _join(f"<b>{_name(lesson)} отменён</b>", f"Был запланирован на {_when(lesson.starts_at, now)}.")


def _homework_deadline_changed(lesson: LessonDTO, now: datetime) -> str:
    return _join(f"<b>Дедлайн {_homework(lesson)} изменён</b>", f"Новый дедлайн: {_when(_deadline(lesson), now)}")


def _homework_removed(lesson: LessonDTO, _now: datetime) -> str:
    return _join(f"<b>{_homework(lesson)} отменено</b>", "Сдавать его не нужно.")


_RENDERERS: dict[ReminderKind, Callable[[LessonDTO, datetime], str]] = {
    ReminderKind.LESSON_UPCOMING: _lesson_upcoming,
    ReminderKind.LESSON_STARTING: _lesson_starting,
    ReminderKind.HOMEWORK_DEADLINE: _homework_deadline,
    ReminderKind.LESSON_RESCHEDULED: _lesson_rescheduled,
    ReminderKind.LESSON_CANCELLED: _lesson_cancelled,
    ReminderKind.HOMEWORK_DEADLINE_CHANGED: _homework_deadline_changed,
    ReminderKind.HOMEWORK_REMOVED: _homework_removed,
}


def _name(lesson: LessonDTO) -> str:
    return f"{_SUBJECTS[lesson.kind]} «{escape(lesson.title)}»"


def _homework(lesson: LessonDTO) -> str:
    return f"ДЗ {_HOMEWORK_TO[lesson.kind]} «{escape(lesson.title)}»"


def _call_link(lesson: LessonDTO) -> str | None:
    if lesson.call_url is None:
        return None
    return f'Подключиться: <a href="{escape(lesson.call_url)}">ссылка на созвон</a>'


def _description(lesson: LessonDTO) -> str | None:
    return f"\n{escape(lesson.description)}" if lesson.description else None


def _deadline(lesson: LessonDTO) -> datetime:
    if lesson.homework_deadline_at is None:
        raise ValueError(f"Lesson {lesson.id} has no homework")
    return lesson.homework_deadline_at


def _join(*lines: str | None) -> str:
    return "\n".join(line for line in lines if line is not None)


def _when(moment: datetime, now: datetime) -> str:
    local = moment.astimezone(BUSINESS_TZ)
    clock = f"{local:%H:%M} (МСК)"
    minutes_left = round((moment - now).total_seconds() / 60)
    if 0 < minutes_left < _RELATIVE_MINUTES:
        return f"через {_in_minutes(minutes_left)}, в {clock}"
    match (local.date() - now.astimezone(BUSINESS_TZ).date()).days:
        case 0:
            day = "сегодня"
        case 1:
            day = "завтра"
        case 2:
            day = "послезавтра"
        case _:
            day = f"{local.day} {_MONTHS[local.month - 1]} ({_WEEKDAYS[local.weekday()]})"
    return f"{day} в {clock}"


def _in_minutes(minutes: int) -> str:
    hours, rest = divmod(minutes, _MINUTES_IN_HOUR)
    if hours == 0:
        return f"{minutes} {_plural(minutes, 'минуту', 'минуты', 'минут')}"
    if rest == 0:
        return "час"
    return f"1 ч {rest} мин"


def _plural(n: int, one: str, few: str, many: str) -> str:
    last_two, last = n % 100, n % 10
    if last == 1 and last_two != _ELEVEN:
        return one
    if last in _FEW_ENDINGS and last_two not in _FEW_EXCEPTIONS:
        return few
    return many


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]
