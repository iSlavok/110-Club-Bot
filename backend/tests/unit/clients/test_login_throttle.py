from unittest.mock import AsyncMock, MagicMock

from app.clients.login_throttle import MAX_FAILURES, WINDOW_SECONDS, RedisLoginThrottle


async def test_blocks_after_max_failures() -> None:
    redis = MagicMock()
    redis.get = AsyncMock(side_effect=[str(MAX_FAILURES - 1).encode(), str(MAX_FAILURES).encode(), None])
    throttle = RedisLoginThrottle(redis)

    assert not await throttle.is_blocked("1.2.3.4")
    assert await throttle.is_blocked("1.2.3.4")
    assert not await throttle.is_blocked("5.6.7.8")


async def test_failure_window_starts_at_first_failure() -> None:
    pipe = MagicMock()
    pipe.execute = AsyncMock()
    redis = MagicMock()
    redis.pipeline.return_value.__aenter__.return_value = pipe
    throttle = RedisLoginThrottle(redis)

    await throttle.register_failure("1.2.3.4")

    pipe.incr.assert_called_once_with("login-failures:1.2.3.4")
    pipe.expire.assert_called_once_with("login-failures:1.2.3.4", WINDOW_SECONDS, nx=True)
    pipe.execute.assert_awaited_once()
