from collections import Counter
from datetime import datetime

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

    async def is_blocked(self, key: str) -> bool:
        return self.failures[key] >= MAX_FAILURES

    async def register_failure(self, key: str) -> None:
        self.failures[key] += 1
