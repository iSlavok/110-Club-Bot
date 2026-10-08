from collections import Counter
from datetime import datetime

from app.clients import LoginThrottleUnavailableError
from app.clients.login_throttle import MAX_FAILURES


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


class FakeLoginThrottle:
    def __init__(self) -> None:
        self.failures: Counter[str] = Counter()
        self.available = True

    async def is_blocked(self, key: str) -> bool:
        self._ensure_available()
        return self.failures[key] >= MAX_FAILURES

    async def register_failure(self, key: str) -> None:
        self._ensure_available()
        self.failures[key] += 1

    def _ensure_available(self) -> None:
        if not self.available:
            raise LoginThrottleUnavailableError
