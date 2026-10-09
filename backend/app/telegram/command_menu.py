from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from loguru import logger

from app import texts

DEFAULT_COMMANDS = (BotCommand(command="start", description=texts.commands.START),)
ADMIN_COMMANDS = (
    *DEFAULT_COMMANDS,
    BotCommand(command="login", description=texts.commands.LOGIN),
    BotCommand(command="adminka", description=texts.commands.ADMINKA),
    BotCommand(command="status", description=texts.commands.STATUS),
)


# The menu is only a hint, so a failed update must not undo the admin change that caused it:
# Telegram errors are logged, and the next bot start syncs every menu again.
class CommandMenu:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def set_default(self) -> None:
        try:
            await self._bot.set_my_commands(list(DEFAULT_COMMANDS), scope=BotCommandScopeDefault())
        except TelegramAPIError:
            logger.exception("Failed to set the default command menu")

    async def show_admin(self, tg_id: int) -> None:
        try:
            await self._bot.set_my_commands(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=tg_id))
        except TelegramAPIError as error:
            logger.warning("Failed to show the admin command menu to {}: {}", tg_id, error)

    async def hide_admin(self, tg_id: int) -> None:
        try:
            await self._bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=tg_id))
        except TelegramAPIError as error:
            logger.warning("Failed to hide the admin command menu from {}: {}", tg_id, error)
