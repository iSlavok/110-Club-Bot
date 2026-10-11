from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from app.telegram.rate_limit import LimiterCache, RateLimit, Timer

USER_LIMIT = RateLimit(rate=1, period=1.0, burst=5)
USER_CACHE_SIZE = 10_000
USER_TTL_SECONDS = 300.0


# Every update holds a database connection until its reply clears the per-chat send limit, so one user flooding
# the bot could take the whole pool. Group chats are not limited: the bot only reacts to service messages there.
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, timer: Timer) -> None:
        self._limiters = LimiterCache(
            private_limit=USER_LIMIT,
            group_limit=USER_LIMIT,
            timer=timer,
            max_size=USER_CACHE_SIZE,
            ttl_seconds=USER_TTL_SECONDS,
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:  # noqa: ANN401 - aiogram middleware contract
        user_id = _limited_user_id(event)
        if user_id is not None and not self._limiters.get(user_id).try_acquire():
            logger.info("Update from user {} dropped: too many updates", user_id)
            return None
        return await handler(event, data)


def _limited_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message):
        if event.chat.type != ChatType.PRIVATE or event.from_user is None:
            return None
        return event.from_user.id
    if isinstance(event, CallbackQuery):
        return event.from_user.id
    return None
