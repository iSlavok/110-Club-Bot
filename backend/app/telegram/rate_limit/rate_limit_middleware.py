from typing import Any

from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import (
    CopyMessage,
    CopyMessages,
    DeleteMessage,
    DeleteMessages,
    EditMessageCaption,
    EditMessageMedia,
    EditMessageReplyMarkup,
    EditMessageText,
    ForwardMessage,
    ForwardMessages,
    PinChatMessage,
    Response,
    SendAnimation,
    SendAudio,
    SendContact,
    SendDice,
    SendDocument,
    SendLocation,
    SendMediaGroup,
    SendMessage,
    SendPaidMedia,
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
    SetMessageReaction,
    TelegramMethod,
    UnpinChatMessage,
)
from loguru import logger

from app.telegram.rate_limit.flood_gate import FloodGate
from app.telegram.rate_limit.limiter_cache import LimiterCache
from app.telegram.rate_limit.timer import Timer
from app.telegram.rate_limit.token_bucket_limiter import RateLimit, TokenBucketLimiter

# Burst + rate is the peak over any one-second window: 5 + 25 stays within Telegram's 30 requests per second.
GLOBAL_LIMIT = RateLimit(rate=25, period=1.0, burst=5)
PRIVATE_CHAT_LIMIT = RateLimit(rate=1, period=1.0, burst=5)
GROUP_CHAT_LIMIT = RateLimit(rate=20, period=60.0, burst=20)
# Edits and deletes have a far looser per-chat limit than new messages; at the send rate every button press would lag.
RELAXED_MULTIPLIER = 5
RETRY_AFTER_BUFFER_SECONDS = 0.5
MAX_ATTEMPTS = 3
LIMITER_CACHE_SIZE = 10_000
LIMITER_TTL_SECONDS = 300.0

type AnyMethod = type[TelegramMethod[Any]]

SEND_METHODS: frozenset[AnyMethod] = frozenset(
    {
        CopyMessage,
        CopyMessages,
        ForwardMessage,
        ForwardMessages,
        SendAnimation,
        SendAudio,
        SendContact,
        SendDice,
        SendDocument,
        SendLocation,
        SendMediaGroup,
        SendMessage,
        SendPaidMedia,
        SendPhoto,
        SendPoll,
        SendSticker,
        SendVenue,
        SendVideo,
        SendVideoNote,
        SendVoice,
    }
)

RELAXED_METHODS: frozenset[AnyMethod] = frozenset(
    {
        DeleteMessage,
        DeleteMessages,
        EditMessageCaption,
        EditMessageMedia,
        EditMessageReplyMarkup,
        EditMessageText,
        PinChatMessage,
        SetMessageReaction,
        UnpinChatMessage,
    }
)


class RateLimitMiddleware(BaseRequestMiddleware):
    def __init__(self, timer: Timer) -> None:
        self._timer = timer
        self._flood_gate = FloodGate(timer)
        self._global_limiter = TokenBucketLimiter(GLOBAL_LIMIT, timer)
        self._send_limiters = self._chat_limiters(multiplier=1)
        self._relaxed_limiters = self._chat_limiters(multiplier=RELAXED_MULTIPLIER)

    def cleanup_expired(self) -> int:
        return self._send_limiters.cleanup_expired() + self._relaxed_limiters.cleanup_expired()

    async def __call__[T](
        self,
        make_request: NextRequestMiddlewareType[T],
        bot: Bot,
        method: TelegramMethod[T],
    ) -> Response[T]:
        chat_id = _chat_id(method)
        method_name = type(method).__name__
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                await self._flood_gate.wait()
                # Chat bucket first: a global token taken before a long per-chat wait is spent with no request.
                chat_limiter = self._chat_limiter(type(method), chat_id)
                if chat_limiter is not None:
                    await chat_limiter.acquire()
                await self._global_limiter.acquire()
                return await make_request(bot, method)
            except TelegramRetryAfter as exc:
                self._flood_gate.pause(exc.retry_after + RETRY_AFTER_BUFFER_SECONDS)
                if attempt == MAX_ATTEMPTS:
                    logger.warning("Flood limit on {} (chat {}): giving up", method_name, chat_id)
                    raise
                logger.warning("Flood limit on {} (chat {}): pausing {}s", method_name, chat_id, exc.retry_after)
        raise AssertionError("unreachable: the last attempt returns or raises")

    def _chat_limiters(self, *, multiplier: int) -> LimiterCache:
        return LimiterCache(
            private_limit=PRIVATE_CHAT_LIMIT.scaled(multiplier),
            group_limit=GROUP_CHAT_LIMIT.scaled(multiplier),
            timer=self._timer,
            max_size=LIMITER_CACHE_SIZE,
            ttl_seconds=LIMITER_TTL_SECONDS,
        )

    def _chat_limiter(self, method_type: AnyMethod, chat_id: int | None) -> TokenBucketLimiter | None:
        if chat_id is None:
            return None
        if method_type in SEND_METHODS:
            return self._send_limiters.get(chat_id)
        if method_type in RELAXED_METHODS:
            return self._relaxed_limiters.get(chat_id)
        return None


def _chat_id(method: TelegramMethod[Any]) -> int | None:
    chat_id: object = getattr(method, "chat_id", None)
    if isinstance(chat_id, int):
        return chat_id
    if isinstance(chat_id, str) and chat_id.removeprefix("-").isdigit():
        return int(chat_id)
    return None
