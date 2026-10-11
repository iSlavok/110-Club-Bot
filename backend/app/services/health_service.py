import asyncio
from collections.abc import Awaitable, Callable

from loguru import logger
from redis.asyncio import Redis

from app.enums import CheckStatus, HealthStatus
from app.queries import SystemQueries
from app.schemas import ReadinessReport

CHECK_TIMEOUT_SECONDS = 2.0


class HealthService:
    def __init__(self, system_queries: SystemQueries, redis: Redis) -> None:
        self._system_queries = system_queries
        self._redis = redis

    async def check_readiness(self) -> ReadinessReport:
        checks = {
            "postgres": await self._run_check("postgres", self._system_queries.ping_database),
            "redis": await self._run_check("redis", self._ping_redis),
        }
        is_ready = all(status is CheckStatus.OK for status in checks.values())
        return ReadinessReport(status=HealthStatus.OK if is_ready else HealthStatus.UNAVAILABLE, checks=checks)

    async def _ping_redis(self) -> None:
        await self._redis.ping()

    @staticmethod
    async def _run_check(name: str, check: Callable[[], Awaitable[None]]) -> CheckStatus:
        try:
            async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
                await check()
        except Exception:  # noqa: BLE001 - any failure means "not ready"; the cause goes to the log
            logger.opt(exception=True).warning("Readiness check {} failed", name)
            return CheckStatus.FAIL
        return CheckStatus.OK
