from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup
from loguru import logger

from app.enums import MessageDelivery
from app.models import User
from app.repositories import UserRepository
from app.utils import Clock


# Every message to a user's private chat goes through here, so a blocked bot is noticed in one place.
class DirectMessageService:
    def __init__(self, user_repository: UserRepository, bot: Bot, clock: Clock) -> None:
        self._user_repository = user_repository
        self._bot = bot
        self._clock = clock

    async def send(self, user: User, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> MessageDelivery:
        try:
            await self._bot.send_message(user.tg_id, text, reply_markup=reply_markup)
        except TelegramForbiddenError:
            logger.info("User {} blocked the bot, message not delivered", user.id)
            if user.bot_blocked_at is None:
                user.bot_blocked_at = self._clock.now()
                await self._user_repository.flush()
            return MessageDelivery.BOT_BLOCKED
        except TelegramAPIError as error:
            logger.warning("Failed to send a message to user {}: {}", user.id, error)
            return MessageDelivery.FAILED
        if user.bot_blocked_at is not None:
            user.bot_blocked_at = None
            await self._user_repository.flush()
        return MessageDelivery.SENT
