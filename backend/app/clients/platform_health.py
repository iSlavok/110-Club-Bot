from typing import Protocol

from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError

_FAILING_KEY = "platform:failing"


# Remembers that the platform is failing, so the owner is alerted on a change, not on every admin request.
# Redis, not the database: a failed request rolls its transaction back, and the mark must survive that.
class PlatformHealth(Protocol):
    # True when the platform was fine before this failure.
    async def mark_failing(self) -> bool: ...

    # True when the platform was failing before this success.
    async def mark_ok(self) -> bool: ...


class RedisPlatformHealth:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # Redis being down only costs an alert: the admin request itself goes on.
    async def mark_failing(self) -> bool:
        try:
            return bool(await self._redis.set(_FAILING_KEY, 1, nx=True))
        except RedisError:
            logger.exception("Cannot remember the platform failure")
            return False

    async def mark_ok(self) -> bool:
        try:
            return bool(await self._redis.delete(_FAILING_KEY))
        except RedisError:
            logger.exception("Cannot clear the platform failure")
            return False
