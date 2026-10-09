import asyncio
from collections import Counter
from datetime import datetime

from app.clients import LoginThrottleUnavailableError, VkClientError, VkUser
from app.clients.login_throttle import MAX_FAILURES


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


# Sleeping moves the clock instead of waiting; sleep(0) still yields so concurrent waiters interleave.
class FakeTimer:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds
        await asyncio.sleep(0)


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


class FakeVkClient:
    def __init__(self) -> None:
        self.screen_names: dict[str, int] = {}
        self.users: dict[int, VkUser] = {}
        # Authorization code -> VK user id that VK ID returns for it.
        self.codes: dict[str, int] = {}
        self.exchanges: list[dict[str, str]] = []
        self.available = True

    def add_user(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        *,
        screen_name: str | None = None,
        deactivated: bool = False,
    ) -> VkUser:
        user = VkUser(id=user_id, first_name=first_name, last_name=last_name, is_deactivated=deactivated)
        self.users[user_id] = user
        if screen_name is not None:
            self.screen_names[screen_name] = user_id
        return user

    async def get_user(self, user_ref: int | str) -> VkUser | None:
        self._ensure_available()
        user_id = self.screen_names.get(user_ref) if isinstance(user_ref, str) else user_ref
        return self.users.get(user_id) if user_id is not None else None

    async def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        device_id: str,
        state: str,
        redirect_uri: str,
    ) -> int:
        self._ensure_available()
        self.exchanges.append(
            {
                "code": code,
                "code_verifier": code_verifier,
                "device_id": device_id,
                "state": state,
                "redirect_uri": redirect_uri,
            },
        )
        if code not in self.codes:
            raise VkClientError("invalid_grant")
        return self.codes[code]

    def _ensure_available(self) -> None:
        if not self.available:
            raise VkClientError("VK is down")
