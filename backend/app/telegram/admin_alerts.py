from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup
from loguru import logger

from app.config import AlertsSettings


# A failed alert must not break the action that raised it: Telegram errors are logged, never propagated.
class AdminAlerts:
    def __init__(self, bot: Bot, settings: AlertsSettings) -> None:
        self._bot = bot
        self._chat_id = settings.chat_id

    async def send(self, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> int | None:
        logger.warning("Admin alert: {}", text)
        if self._chat_id is None:
            return None
        try:
            message = await self._bot.send_message(self._chat_id, text, reply_markup=reply_markup)
        except TelegramAPIError:
            logger.exception("Failed to send the admin alert")
            return None
        return message.message_id

    # Without reply_markup Telegram drops the buttons of the message.
    async def edit(self, message_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
        logger.info("Admin alert {} edited: {}", message_id, text)
        if self._chat_id is None:
            return
        try:
            await self._bot.edit_message_text(
                text=text,
                chat_id=self._chat_id,
                message_id=message_id,
                reply_markup=reply_markup,
            )
        except TelegramAPIError:
            logger.exception("Failed to edit admin alert {}", message_id)
