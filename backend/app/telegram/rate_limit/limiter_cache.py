from collections import OrderedDict

from app.telegram.rate_limit.timer import Timer
from app.telegram.rate_limit.token_bucket_limiter import RateLimit, TokenBucketLimiter


class LimiterCache:
    def __init__(
        self,
        *,
        private_limit: RateLimit,
        group_limit: RateLimit,
        timer: Timer,
        max_size: int,
        ttl_seconds: float,
    ) -> None:
        self._private_limit = private_limit
        self._group_limit = group_limit
        self._timer = timer
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._limiters: OrderedDict[int, tuple[TokenBucketLimiter, float]] = OrderedDict()

    def __len__(self) -> int:
        return len(self._limiters)

    def get(self, chat_id: int) -> TokenBucketLimiter:
        now = self._timer.monotonic()
        if chat_id in self._limiters:
            limiter, _ = self._limiters[chat_id]
            self._limiters.move_to_end(chat_id)
        else:
            # Telegram ids: users are positive, groups and channels negative.
            limit = self._private_limit if chat_id > 0 else self._group_limit
            limiter = TokenBucketLimiter(limit, self._timer)
        self._limiters[chat_id] = (limiter, now)
        while len(self._limiters) > self._max_size:
            self._limiters.popitem(last=False)
        return limiter

    def cleanup_expired(self) -> int:
        now = self._timer.monotonic()
        expired = [chat_id for chat_id, (_, last_used) in self._limiters.items() if now - last_used > self._ttl_seconds]
        for chat_id in expired:
            del self._limiters[chat_id]
        return len(expired)
