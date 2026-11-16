from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from loguru import logger

from app import texts
from app.models import Reminder
from app.repositories import ReminderRepository
from app.schemas import ReminderButton, ReminderWithLessonDTO
from app.telegram import reminder_keyboard
from app.utils import Clock

STALE_BATCH_SIZE = 50
# Long enough for any call: the lesson keeps no end time, and a call button left later only clutters the topic.
CALL_BUTTON_LIFETIME = timedelta(hours=3)
_TRANSIENT_ERRORS = (TelegramRetryAfter, TelegramNetworkError, TelegramServerError)


# Keeps the buttons of sent reminders in line with their lesson: links follow its edits, the call button goes
# after the call, all buttons go with a cancelled lesson.
class ReminderButtonsService:
    def __init__(self, reminder_repository: ReminderRepository, bot: Bot, clock: Clock) -> None:
        self._reminder_repository = reminder_repository
        self._bot = bot
        self._clock = clock

    async def list_stale_ids(self) -> list[int]:
        return await self._reminder_repository.list_stale_button_ids(
            now=self._clock.now(),
            call_lifetime=CALL_BUTTON_LIFETIME,
            limit=STALE_BATCH_SIZE,
        )

    async def sync(self, reminder_id: int) -> None:
        reminder = await self._reminder_repository.get_with_club_and_lesson(reminder_id)
        if reminder is None or reminder.lesson is None:
            return
        now = self._clock.now()
        dto = ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder)
        wanted = _wanted_buttons(dto, now)
        if wanted != dto.buttons and not await self._edit(reminder, wanted):
            return
        reminder.buttons = [button.model_dump() for button in wanted]
        reminder.buttons_checked_at = now
        reminder.buttons_lesson_version = reminder.lesson.updated_at
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
        except TelegramBadRequest as error:
            # Messages sent before the buttons were stored are edited blindly: most already show the right ones.
            if "message is not modified" not in error.message:
                logger.warning("Buttons of reminder {} cannot be edited: {}", reminder.id, error)
        except TelegramAPIError as error:
            logger.warning("Buttons of reminder {} cannot be edited: {}", reminder.id, error)
        return True


def _wanted_buttons(reminder: ReminderWithLessonDTO, now: datetime) -> list[ReminderButton]:
    lesson = reminder.lesson
    if lesson is None or lesson.is_cancelled:
        return []
    with_call = now < lesson.starts_at + CALL_BUTTON_LIFETIME
    return texts.reminders.lesson_buttons(reminder.kind, lesson, with_call=with_call)
