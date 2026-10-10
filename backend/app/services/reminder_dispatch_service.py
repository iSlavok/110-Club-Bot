from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import LinkPreviewOptions
from loguru import logger

from app import texts
from app.enums import ReminderKind, ReminderStatus
from app.models import Reminder
from app.repositories import ReminderRepository
from app.schemas import ReminderWithLessonDTO
from app.telegram import AdminAlerts
from app.utils import Clock

DUE_BATCH_SIZE = 50
MAX_SEND_ATTEMPTS = 3
ERROR_MAX_LEN = 1000
# A reminder delayed by downtime is still useful a little after the start: the call link is in it.
LESSON_LATENESS = timedelta(minutes=5)
NOTICE_LATENESS = timedelta(hours=1)
NOTICE_KINDS = frozenset(
    {
        ReminderKind.LESSON_RESCHEDULED,
        ReminderKind.LESSON_CANCELLED,
        ReminderKind.HOMEWORK_DEADLINE_CHANGED,
        ReminderKind.HOMEWORK_REMOVED,
    },
)


class ReminderDispatchService:
    def __init__(
        self,
        reminder_repository: ReminderRepository,
        bot: Bot,
        admin_alerts: AdminAlerts,
        clock: Clock,
    ) -> None:
        self._reminder_repository = reminder_repository
        self._bot = bot
        self._admin_alerts = admin_alerts
        self._clock = clock

    async def list_due_ids(self) -> list[int]:
        return await self._reminder_repository.list_due_ids(now=self._clock.now(), limit=DUE_BATCH_SIZE)

    # A crash between the send and the commit of this scope resends the message: rare enough to accept.
    async def dispatch(self, reminder_id: int) -> None:
        now = self._clock.now()
        reminder = await self._reminder_repository.get_due_for_update(reminder_id=reminder_id, now=now)
        if reminder is None:
            return
        club = reminder.club
        skip_reason = _skip_reason(reminder, now)
        if skip_reason is not None:
            reminder.status = ReminderStatus.SKIPPED
            reminder.error = skip_reason
        elif club.chat_id is None or club.reminders_topic_id is None:
            await self._fail(reminder, "Club has no chat or reminders topic")
        else:
            await self._send(reminder, chat_id=club.chat_id, topic_id=club.reminders_topic_id, now=now)
        await self._reminder_repository.flush()

    # For errors outside Telegram (a rendering bug): without a limit such a reminder would crash every minute.
    async def record_failure(self, reminder_id: int, error: str) -> None:
        reminder = await self._reminder_repository.get_with_club_and_lesson(reminder_id)
        if reminder is None or reminder.status != ReminderStatus.PENDING:
            return
        await self._register_failed_attempt(reminder, error)
        await self._reminder_repository.flush()

    async def _send(self, reminder: Reminder, *, chat_id: int, topic_id: int, now: datetime) -> None:
        text = texts.reminders.render(ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder), now)
        try:
            message = await self._bot.send_message(
                chat_id=chat_id,
                text=text,
                message_thread_id=topic_id,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        except TelegramRetryAfter as error:
            # The session middleware has already retried: the next run picks the reminder up after the pause.
            reminder.send_at = now + timedelta(seconds=error.retry_after)
            logger.warning("Reminder {} hit the flood limit, postponed by {} s", reminder.id, error.retry_after)
        except TelegramAPIError as error:
            logger.warning("Reminder {} was not sent: {}", reminder.id, error)
            await self._register_failed_attempt(reminder, str(error))
        else:
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = now
            reminder.message_id = message.message_id
            reminder.attempts += 1
            reminder.error = None

    async def _register_failed_attempt(self, reminder: Reminder, error: str) -> None:
        reminder.attempts += 1
        if reminder.attempts >= MAX_SEND_ATTEMPTS:
            await self._fail(reminder, error)
        else:
            reminder.error = error[:ERROR_MAX_LEN]

    async def _fail(self, reminder: Reminder, error: str) -> None:
        reminder.status = ReminderStatus.FAILED
        reminder.error = error[:ERROR_MAX_LEN]
        dto = ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder)
        await self._admin_alerts.send(texts.alerts.reminder_failed(reminder.club.title, dto))


def _skip_reason(reminder: Reminder, now: datetime) -> str | None:
    lesson = reminder.lesson
    if not reminder.club.is_active:
        return "Club is inactive"
    if reminder.kind is ReminderKind.HOMEWORK_DEADLINE_CHANGED and lesson.homework_deadline_at is None:
        return "Homework was removed"
    if reminder.kind in NOTICE_KINDS:
        return "Notice is over an hour late" if now > reminder.send_at + NOTICE_LATENESS else None
    if lesson.is_cancelled:
        return "Lesson is cancelled"
    if reminder.kind is ReminderKind.HOMEWORK_DEADLINE:
        deadline = lesson.homework_deadline_at
        return "Homework deadline has passed" if deadline is None or now > deadline else None
    return "Lesson has already started" if now > lesson.starts_at + LESSON_LATENESS else None
