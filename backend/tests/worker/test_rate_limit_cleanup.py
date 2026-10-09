from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.methods import SendMessage

from app.telegram import RateLimitMiddleware
from tests.fakes import FakeTimer
from worker.jobs import cleanup_rate_limiters


async def test_drops_idle_chat_limiters() -> None:
    timer = FakeTimer()
    rate_limit = RateLimitMiddleware(timer)
    await rate_limit(AsyncMock(), AsyncMock(spec=Bot), SendMessage(chat_id=42, text="hi"))
    timer.now += 301

    await cleanup_rate_limiters(rate_limit)

    assert rate_limit.cleanup_expired() == 0
