from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.methods import DeleteMyCommands, SetMyCommands
from aiogram.types import (
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeChatMember,
    BotCommandScopeDefault,
)

from app.telegram import ADMIN_COMMANDS, CHAT_ADMIN_COMMANDS, DEFAULT_COMMANDS, CommandMenu


def _menu() -> tuple[CommandMenu, AsyncMock]:
    bot = AsyncMock(spec=Bot)
    return CommandMenu(bot), bot


def test_admin_menu_extends_the_default_one() -> None:
    assert ADMIN_COMMANDS[: len(DEFAULT_COMMANDS)] == DEFAULT_COMMANDS
    assert [command.command for command in ADMIN_COMMANDS] == [
        "start",
        "vk",
        "status",
        "schedule",
        "login",
        "adminka",
        "summary",
    ]


def test_chat_admin_menu_is_an_ephemeral_vk_lookup() -> None:
    assert [(command.command, command.is_ephemeral) for command in CHAT_ADMIN_COMMANDS] == [("vk", True)]


async def test_set_default_keeps_group_chats_without_commands() -> None:
    menu, bot = _menu()

    await menu.set_default()

    bot.set_my_commands.assert_awaited_once_with(list(DEFAULT_COMMANDS), scope=BotCommandScopeAllPrivateChats())
    bot.delete_my_commands.assert_awaited_once_with(scope=BotCommandScopeDefault())


async def test_show_admin_scopes_the_menu_to_the_admin_chat() -> None:
    menu, bot = _menu()

    await menu.show_admin(42)

    bot.set_my_commands.assert_awaited_once_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=42))


async def test_hide_admin_falls_back_to_the_default_menu() -> None:
    menu, bot = _menu()

    await menu.hide_admin(42)

    bot.delete_my_commands.assert_awaited_once_with(scope=BotCommandScopeChat(chat_id=42))


async def test_chat_admin_menu_is_scoped_to_the_admin_in_the_chat() -> None:
    menu, bot = _menu()

    await menu.show_chat_admin(-100, 42)
    await menu.hide_chat_admin(-100, 42)

    scope = BotCommandScopeChatMember(chat_id=-100, user_id=42)
    bot.set_my_commands.assert_awaited_once_with(list(CHAT_ADMIN_COMMANDS), scope=scope)
    bot.delete_my_commands.assert_awaited_once_with(scope=scope)


async def test_telegram_errors_are_not_raised() -> None:
    menu, bot = _menu()
    bot.set_my_commands.side_effect = TelegramBadRequest(SetMyCommands(commands=[]), "chat not found")
    bot.delete_my_commands.side_effect = TelegramForbiddenError(DeleteMyCommands(), "bot was blocked by the user")

    await menu.set_default()
    await menu.show_admin(42)
    await menu.hide_admin(42)
    await menu.show_chat_admin(-100, 42)
    await menu.hide_chat_admin(-100, 42)

    assert bot.set_my_commands.await_count == 3
    assert bot.delete_my_commands.await_count == 2
