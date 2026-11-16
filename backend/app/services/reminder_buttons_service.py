from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramRetryAfter, TelegramServerError
from loguru import logger

from app import texts
from app.models import Reminder
from app.repositories import ReminderRepository
from app.schemas import ReminderButton, ReminderWithLessonDTO
from app.telegram import reminder_keyboard
from app.utils import Clock

OUTDATED_BATCH_SIZE = 50
# Long enough for any call: the lesson keeps no end time, and a call button left later only clutters the topic.
CALL_BUTTON_LIFETIME = timedelta(hours=3)
_TRANSIENT_ERRORS = (TelegramRetryAfter, TelegramNetworkError, TelegramServerError)


# Edits the keyboards of sent reminders: the call button goes after the call, all buttons go with a cancelled lesson.
class ReminderButtonsService:
    def __init__(self, reminder_repository: ReminderRepository, bot: Bot, clock: Clock) -> None:
        self._reminder_repository = reminder_repository
        self._bot = bot
        self._clock = clock

    async def list_outdated_ids(self) -> list[int]:
        return await self._reminder_repository.list_outdated_button_ids(
            call_started_before=self._clock.now() - CALL_BUTTON_LIFETIME,
            limit=OUTDATED_BATCH_SIZE,
        )

    async def trim(self, reminder_id: int) -> None:
        reminder = await self._reminder_repository.get_with_club_and_lesson(reminder_id)
        if reminder is None or reminder.buttons_removed_at is not None:
            return
        dto = ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder)
        lesson = dto.lesson
        if lesson is None:
            return
        shown = texts.reminders.lesson_buttons(dto.kind, lesson, with_call=reminder.call_button_removed_at is None)
        cancelled = lesson.is_cancelled
        wanted = [] if cancelled else texts.reminders.lesson_buttons(dto.kind, lesson, with_call=False)
        if wanted != shown and not await self._edit(reminder, wanted):
            return
        now = self._clock.now()
        reminder.call_button_removed_at = reminder.call_button_removed_at or now
        if cancelled:
            reminder.buttons_removed_at = now
        await self._reminder_repository.flush()

    # False: worth another try on the next run. A message that is gone or cannot be edited is left as it is.
    async def _edit(self, reminder: Reminder, buttons: list[ReminderButton]) -> bool:
        chat_id = reminder.club.chat_id
        if chat_id is None or reminder.message_id is None:
            return True
        try:
            await self._bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=reminder.message_id,
                reply_markup=reminder_keyboard(buttons),
            )
        except _TRANSIENT_ERRORS as error:
            logger.warning("Buttons of reminder {} were not edited, will retry: {}", reminder.id, error)
            return False
        except TelegramAPIError as error:
            logger.warning("Buttons of reminder {} cannot be edited: {}", reminder.id, error)
        return True
