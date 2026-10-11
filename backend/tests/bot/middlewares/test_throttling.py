from datetime import UTC, datetime
from unittest.mock import AsyncMock

from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Chat, Message, User

from bot.middlewares import ThrottlingMiddleware
from bot.middlewares.throttling import USER_LIMIT
from tests.fakes import FakeTimer

USER_ID = 100_001


def _message(user_id: int = USER_ID, chat_type: ChatType = ChatType.PRIVATE) -> Message:
    chat_id = user_id if chat_type is ChatType.PRIVATE else -100500
    return Message(
        message_id=1,
        date=datetime(2026, 10, 1, tzinfo=UTC),
        chat=Chat(id=chat_id, type=chat_type),
        from_user=User(id=user_id, is_bot=False, first_name="Student"),
        text="/status",
    )


def _callback(user_id: int = USER_ID) -> CallbackQuery:
    return CallbackQuery(
        id="1",
        from_user=User(id=user_id, is_bot=False, first_name="Student"),
        chat_instance="chat",
    )


async def _passed(middleware: ThrottlingMiddleware, event: Message | CallbackQuery, times: int) -> int:
    handler = AsyncMock()
    for _ in range(times):
        await middleware(handler, event, {})
    return handler.await_count


async def test_updates_beyond_the_burst_are_dropped_until_tokens_refill() -> None:
    timer = FakeTimer()
    middleware = ThrottlingMiddleware(timer)

    assert await _passed(middleware, _message(), USER_LIMIT.burst + 3) == USER_LIMIT.burst

    timer.now += 1.0
    assert await _passed(middleware, _message(), 2) == 1


async def test_each_user_has_their_own_limit() -> None:
    middleware = ThrottlingMiddleware(FakeTimer())
    await _passed(middleware, _message(), USER_LIMIT.burst)

    assert await _passed(middleware, _message(user_id=USER_ID + 1), 1) == 1


async def test_button_presses_share_the_limit_with_messages() -> None:
    middleware = ThrottlingMiddleware(FakeTimer())
    await _passed(middleware, _message(), USER_LIMIT.burst)

    assert await _passed(middleware, _callback(), 1) == 0


async def test_group_chat_messages_are_not_limited() -> None:
    middleware = ThrottlingMiddleware(FakeTimer())

    assert (
        await _passed(middleware, _message(chat_type=ChatType.SUPERGROUP), USER_LIMIT.burst + 3) == USER_LIMIT.burst + 3
    )
