from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import SendMessage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from app.config import AlertsSettings
from app.telegram import AdminAlerts

ALERTS_CHAT = -100777


@pytest.fixture
def logs() -> Iterator[list[str]]:
    messages: list[str] = []
    handler_id = logger.add(messages.append, format="{message}")
    yield messages
    logger.remove(handler_id)


@pytest.fixture
def bot() -> AsyncMock:
    bot = AsyncMock(spec=Bot)
    bot.send_message.return_value = MagicMock(message_id=55)
    return bot


def _network_error() -> TelegramNetworkError:
    return TelegramNetworkError(method=SendMessage(chat_id=ALERTS_CHAT, text="x"), message="timeout")


async def test_send_posts_to_the_alerts_chat(bot) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="OK", callback_data="ok")]])

    message_id = await AdminAlerts(bot, AlertsSettings(chat_id=ALERTS_CHAT)).send("Синк упал", keyboard)

    assert message_id == 55
    bot.send_message.assert_awaited_once_with(ALERTS_CHAT, "Синк упал", reply_markup=keyboard)


async def test_send_without_chat_only_logs(bot, logs) -> None:
    message_id = await AdminAlerts(bot, AlertsSettings()).send("Синк упал")

    assert message_id is None
    bot.send_message.assert_not_awaited()
    assert any("Синк упал" in line for line in logs)


async def test_send_swallows_telegram_errors(bot) -> None:
    bot.send_message.side_effect = _network_error()

    message_id = await AdminAlerts(bot, AlertsSettings(chat_id=ALERTS_CHAT)).send("Синк упал")

    assert message_id is None


async def test_edit_replaces_the_alert_text(bot) -> None:
    await AdminAlerts(bot, AlertsSettings(chat_id=ALERTS_CHAT)).edit(55, "Подтверждено")

    bot.edit_message_text.assert_awaited_once_with(text="Подтверждено", chat_id=ALERTS_CHAT, message_id=55)


async def test_edit_without_chat_does_nothing(bot) -> None:
    await AdminAlerts(bot, AlertsSettings()).edit(55, "Подтверждено")

    bot.edit_message_text.assert_not_awaited()


async def test_edit_swallows_telegram_errors(bot) -> None:
    bot.edit_message_text.side_effect = _network_error()

    await AdminAlerts(bot, AlertsSettings(chat_id=ALERTS_CHAT)).edit(55, "Подтверждено")

    bot.edit_message_text.assert_awaited_once()
