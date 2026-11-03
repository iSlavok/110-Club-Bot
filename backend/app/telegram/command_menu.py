from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeChatMember,
    BotCommandScopeDefault,
)
from loguru import logger

from app import texts

DEFAULT_COMMANDS = (
    BotCommand(command="start", description=texts.commands.START),
    BotCommand(command="vk", description=texts.commands.VK),
    BotCommand(command="status", description=texts.commands.STATUS),
    BotCommand(command="schedule", description=texts.commands.SCHEDULE),
)
ADMIN_COMMANDS = (
    *DEFAULT_COMMANDS,
    BotCommand(command="login", description=texts.commands.LOGIN),
    BotCommand(command="adminka", description=texts.commands.ADMINKA),
    BotCommand(command="summary", description=texts.commands.SUMMARY),
)
# Ephemeral: the command and the answer stay between the admin and the bot, the club chat sees neither.
CHAT_ADMIN_COMMANDS = (BotCommand(command="vk", description=texts.commands.VK_LOOKUP, is_ephemeral=True),)


# The menu is only a hint, so a failed update must not undo the admin change that caused it:
# Telegram errors are logged, and the next bot start syncs every menu again.
class CommandMenu:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    # The default scope covers group chats too, where students must see no commands at all.
    async def set_default(self) -> None:
        try:
            await self._bot.set_my_commands(list(DEFAULT_COMMANDS), scope=BotCommandScopeAllPrivateChats())
            await self._bot.delete_my_commands(scope=BotCommandScopeDefault())
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

    async def show_chat_admin(self, chat_id: int, tg_id: int) -> None:
        scope = BotCommandScopeChatMember(chat_id=chat_id, user_id=tg_id)
        try:
            await self._bot.set_my_commands(list(CHAT_ADMIN_COMMANDS), scope=scope)
        except TelegramAPIError as error:
            logger.warning("Failed to show the chat admin menu to {} in {}: {}", tg_id, chat_id, error)

    async def hide_chat_admin(self, chat_id: int, tg_id: int) -> None:
        try:
            await self._bot.delete_my_commands(scope=BotCommandScopeChatMember(chat_id=chat_id, user_id=tg_id))
        except TelegramAPIError as error:
            logger.warning("Failed to hide the chat admin menu from {} in {}: {}", tg_id, chat_id, error)
