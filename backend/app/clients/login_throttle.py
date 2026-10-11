from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.clients.exceptions import LoginThrottleUnavailableError

MAX_FAILURES = 10
WINDOW_SECONDS = 15 * 60


class LoginThrottle(Protocol):
    async def is_blocked(self, key: str) -> bool: ...

    async def register_failure(self, key: str) -> None: ...


class RedisLoginThrottle:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def is_blocked(self, key: str) -> bool:
        try:
            failures = await self._redis.get(self._key(key))
        except RedisError as error:
            raise LoginThrottleUnavailableError from error
        return int(failures or 0) >= MAX_FAILURES

    async def register_failure(self, key: str) -> None:
        # The window starts at the first failure and is not extended by later ones.
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.incr(self._key(key))
                pipe.expire(self._key(key), WINDOW_SECONDS, nx=True)
                await pipe.execute()
        except RedisError as error:
            raise LoginThrottleUnavailableError from error

    @staticmethod
    def _key(key: str) -> str:
        return f"login-failures:{key}"
