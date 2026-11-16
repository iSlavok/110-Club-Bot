from unittest.mock import AsyncMock, MagicMock

from redis.exceptions import ConnectionError as RedisConnectionError

from app.clients import RedisPlatformHealth


async def test_only_the_first_failure_is_news() -> None:
    redis = MagicMock()
    redis.set = AsyncMock(side_effect=[True, None])
    health = RedisPlatformHealth(redis)

    assert await health.mark_failing()
    assert not await health.mark_failing()
    redis.set.assert_awaited_with("platform:failing", 1, nx=True)


async def test_success_is_news_only_after_a_failure() -> None:
    redis = MagicMock()
    redis.delete = AsyncMock(side_effect=[1, 0])
    health = RedisPlatformHealth(redis)

    assert await health.mark_ok()
    assert not await health.mark_ok()


async def test_redis_down_costs_only_the_alert() -> None:
    redis = MagicMock()
    redis.set = AsyncMock(side_effect=RedisConnectionError)
    redis.delete = AsyncMock(side_effect=RedisConnectionError)
    health = RedisPlatformHealth(redis)

    assert not await health.mark_failing()
    assert not await health.mark_ok()
