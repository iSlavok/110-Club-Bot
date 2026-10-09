import asyncio
from dataclasses import dataclass
from typing import Self

from app.telegram.rate_limit.timer import Timer


@dataclass(frozen=True, slots=True)
class RateLimit:
    rate: int
    period: float
    burst: int

    def __post_init__(self) -> None:
        if self.rate <= 0 or self.period <= 0 or self.burst <= 0:
            raise ValueError("Rate, period and burst must be positive")

    def scaled(self, multiplier: int) -> Self:
        return type(self)(rate=self.rate * multiplier, period=self.period, burst=self.burst * multiplier)


# A bucket, not a fixed interval: one user action makes several calls to the same chat, and Telegram limits
# are averages, so a short burst passes at once and only a sustained excess is slowed down.
class TokenBucketLimiter:
    def __init__(self, limit: RateLimit, timer: Timer) -> None:
        self._capacity = float(limit.burst)
        self._refill_per_second = limit.rate / limit.period
        self._timer = timer
        self._tokens = self._capacity
        self._updated = timer.monotonic()
        # Waiters queue on the lock, so tokens are handed out in arrival order.
        self._lock = asyncio.Lock()

    @property
    def tokens(self) -> float:
        return min(self._capacity, self._tokens + (self._timer.monotonic() - self._updated) * self._refill_per_second)

    async def acquire(self) -> None:
        async with self._lock:
            self._refill()
            if self._tokens < 1.0:
                await self._timer.sleep((1.0 - self._tokens) / self._refill_per_second)
                self._refill()
            # Taken even if rounding left 0.999...: the debt is repaid by the next waiter, a re-check could spin.
            self._tokens -= 1.0

    def _refill(self) -> None:
        self._tokens = self.tokens
        self._updated = self._timer.monotonic()
