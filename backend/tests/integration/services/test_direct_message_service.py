from datetime import UTC, datetime

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from aiogram.methods import SendMessage

from app.enums import MessageDelivery
from app.services import DirectMessageService
from tests.factories import make_user
from tests.providers import DEFAULT_NOW

BLOCKED_BEFORE = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
async def service(request_container) -> DirectMessageService:
    return await request_container.get(DirectMessageService)


def _forbidden() -> TelegramForbiddenError:
    return TelegramForbiddenError(method=SendMessage(chat_id=1, text="x"), message="bot was blocked by the user")


async def test_delivered_message_clears_a_stale_block(service, db_session, bot) -> None:
    user = await make_user(db_session, bot_blocked_at=BLOCKED_BEFORE)

    delivery = await service.send(user, "Привет")

    assert delivery is MessageDelivery.SENT
    bot.send_message.assert_awaited_once_with(user.tg_id, "Привет", reply_markup=None)
    assert user.bot_blocked_at is None


async def test_blocked_bot_marks_the_user_once(service, db_session, bot) -> None:
    bot.send_message.side_effect = _forbidden()
    fresh = await make_user(db_session)
    known = await make_user(db_session, bot_blocked_at=BLOCKED_BEFORE)

    assert await service.send(fresh, "Привет") is MessageDelivery.BOT_BLOCKED
    assert await service.send(known, "Привет") is MessageDelivery.BOT_BLOCKED

    assert fresh.bot_blocked_at == DEFAULT_NOW
    assert known.bot_blocked_at == BLOCKED_BEFORE


async def test_other_errors_fail_without_marking_a_block(service, db_session, bot) -> None:
    bot.send_message.side_effect = TelegramNetworkError(method=SendMessage(chat_id=1, text="x"), message="timeout")
    user = await make_user(db_session)

    assert await service.send(user, "Привет") is MessageDelivery.FAILED
    assert user.bot_blocked_at is None
