from collections.abc import Callable
from datetime import datetime, timedelta
from html import escape
from typing import Protocol

from app.enums import LessonKind, ReminderKind
from app.schemas import ReminderWithLessonDTO
from app.types import telegram_html_to_text
from app.utils import BUSINESS_TZ

MONTHS = (
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
WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
KIND_LABELS = {
    ReminderKind.LESSON_UPCOMING: "напоминание об уроке",
    ReminderKind.LESSON_STARTING: "урок начинается",
    ReminderKind.HOMEWORK_DEADLINE: "дедлайн ДЗ",
    ReminderKind.LESSON_RESCHEDULED: "перенос урока",
    ReminderKind.LESSON_CANCELLED: "отмена урока",
    ReminderKind.HOMEWORK_DEADLINE_CHANGED: "новый дедлайн ДЗ",
    ReminderKind.HOMEWORK_REMOVED: "отмена ДЗ",
    ReminderKind.MESSAGE: "сообщение",
}
_SUBJECTS = {LessonKind.LESSON: "Урок", LessonKind.CURATOR_CALL: "Созвон с куратором"}
_HOMEWORK_TO = {LessonKind.LESSON: "к уроку", LessonKind.CURATOR_CALL: "к созвону"}
# Closer than this, "через 45 минут" reads better than a clock time.
_RELATIVE_MINUTES = 120
_MINUTES_IN_HOUR = 60
# Russian plural forms: 1 минуту, 2-4 минуты, 5-20 минут; 11-14 always take the "many" form.
_ELEVEN = 11
_FEW_ENDINGS = frozenset({2, 3, 4})
_FEW_EXCEPTIONS = frozenset({12, 13, 14})
# The dispatch run lags behind send_at by seconds: counted from the moment itself, "через час" would read
# "через 59 минут". A longer delay (downtime) is counted from the real moment, so the text stays true.
_ON_TIME_LAG = timedelta(minutes=5)
_SUBJECT_MAX_LEN = 40


# What a message needs from a lesson: a saved LessonDTO or a draft from the lesson form.
class ReminderLesson(Protocol):
    @property
    def kind(self) -> LessonKind: ...
    @property
    def title(self) -> str: ...
    @property
    def description(self) -> str | None: ...
    @property
    def starts_at(self) -> datetime: ...
    @property
    def call_url(self) -> str | None: ...
    @property
    def homework_deadline_at(self) -> datetime | None: ...


def render(reminder: ReminderWithLessonDTO, sent_at: datetime) -> str:
    if reminder.lesson is None:
        if reminder.text is None:
            raise ValueError("Reminder has neither a lesson nor a text")
        return reminder.text
    send_at = reminder.send_at
    now = send_at if send_at <= sent_at <= send_at + _ON_TIME_LAG else sent_at
    return render_message(reminder.kind, reminder.lesson, now)


# What a reminder is about, for admin lists and alerts: the lesson or the start of the message.
def subject(reminder: ReminderWithLessonDTO) -> str:
    if reminder.lesson is not None:
        return f"«{escape(reminder.lesson.title)}»"
    text = " ".join(telegram_html_to_text(reminder.text or "").split())
    if len(text) > _SUBJECT_MAX_LEN:
        text = text[:_SUBJECT_MAX_LEN] + "…"
    return f"«{escape(text)}»"


def render_message(kind: ReminderKind, lesson: ReminderLesson, now: datetime) -> str:
    return _RENDERERS[kind](lesson, now)


# now is the moment relative times ("через час") are counted from.
def _lesson_upcoming(lesson: ReminderLesson, now: datetime) -> str:
    return _join(
        f"<b>{_name(lesson)}</b>",
        _capitalize(_when(lesson.starts_at, now)),
        _call_link(lesson),
        _description(lesson),
    )


def _lesson_starting(lesson: ReminderLesson, _now: datetime) -> str:
    return _join(f"<b>{_name(lesson)} начинается</b>", _call_link(lesson), _description(lesson))


def _homework_deadline(lesson: ReminderLesson, now: datetime) -> str:
    return _join(f"<b>{_homework(lesson)}</b>", f"Дедлайн — {_when(_deadline(lesson), now)}")


def _lesson_rescheduled(lesson: ReminderLesson, now: datetime) -> str:
    return _join(
        f"<b>{_name(lesson)} перенесён</b>",
        f"Новое время: {_when(lesson.starts_at, now)}",
        _call_link(lesson),
    )


def _lesson_cancelled(lesson: ReminderLesson, now: datetime) -> str:
    return _join(f"<b>{_name(lesson)} отменён</b>", f"Был запланирован на {_when(lesson.starts_at, now)}.")


def _homework_deadline_changed(lesson: ReminderLesson, now: datetime) -> str:
    return _join(f"<b>Дедлайн {_homework(lesson)} изменён</b>", f"Новый дедлайн — {_when(_deadline(lesson), now)}")


def _homework_removed(lesson: ReminderLesson, _now: datetime) -> str:
    return _join(f"<b>{_homework(lesson)} отменено</b>", "Сдавать его не нужно.")


_RENDERERS: dict[ReminderKind, Callable[[ReminderLesson, datetime], str]] = {
    ReminderKind.LESSON_UPCOMING: _lesson_upcoming,
    ReminderKind.LESSON_STARTING: _lesson_starting,
    ReminderKind.HOMEWORK_DEADLINE: _homework_deadline,
    ReminderKind.LESSON_RESCHEDULED: _lesson_rescheduled,
    ReminderKind.LESSON_CANCELLED: _lesson_cancelled,
    ReminderKind.HOMEWORK_DEADLINE_CHANGED: _homework_deadline_changed,
    ReminderKind.HOMEWORK_REMOVED: _homework_removed,
}


def _name(lesson: ReminderLesson) -> str:
    return f"{_SUBJECTS[lesson.kind]} «{escape(lesson.title)}»"


def _homework(lesson: ReminderLesson) -> str:
    return f"ДЗ {_HOMEWORK_TO[lesson.kind]} «{escape(lesson.title)}»"


def short_time(moment: datetime) -> str:
    return f"{moment.astimezone(BUSINESS_TZ):%d.%m %H:%M}"


def _call_link(lesson: ReminderLesson) -> str | None:
    if lesson.call_url is None:
        return None
    return f'Подключиться: <a href="{escape(lesson.call_url)}">ссылка на созвон</a>'


def _description(lesson: ReminderLesson) -> str | None:
    return f"\n{escape(lesson.description)}" if lesson.description else None


def _deadline(lesson: ReminderLesson) -> datetime:
    if lesson.homework_deadline_at is None:
        raise ValueError("Lesson has no homework")
    return lesson.homework_deadline_at


def _join(*lines: str | None) -> str:
    return "\n".join(line for line in lines if line is not None)


def _when(moment: datetime, now: datetime) -> str:
    local = moment.astimezone(BUSINESS_TZ)
    clock = f"{local:%H:%M}"
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
            day = f"{local.day} {MONTHS[local.month - 1]} ({WEEKDAYS[local.weekday()]})"
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
