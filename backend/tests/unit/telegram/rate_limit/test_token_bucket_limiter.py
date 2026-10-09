import asyncio

import pytest

from app.telegram.rate_limit import RateLimit, TokenBucketLimiter
from tests.fakes import FakeTimer

ONE_PER_SECOND_BURST_FIVE = RateLimit(rate=1, period=1.0, burst=5)


@pytest.mark.parametrize(("rate", "period", "burst"), [(0, 1.0, 1), (-1, 1.0, 1), (1, 0.0, 1), (1, 1.0, 0)])
def test_rate_limit_rejects_non_positive_values(rate: int, period: float, burst: int) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        RateLimit(rate=rate, period=period, burst=burst)


def test_scaled_multiplies_rate_and_burst() -> None:
    assert RateLimit(rate=20, period=60.0, burst=20).scaled(5) == RateLimit(rate=100, period=60.0, burst=100)


async def test_burst_passes_without_waiting() -> None:
    timer = FakeTimer()
    limiter = TokenBucketLimiter(ONE_PER_SECOND_BURST_FIVE, timer)

    for _ in range(5):
        await limiter.acquire()

    assert timer.sleeps == []


async def test_waits_for_the_next_token_once_burst_is_spent() -> None:
    timer = FakeTimer()
    limiter = TokenBucketLimiter(ONE_PER_SECOND_BURST_FIVE, timer)
    for _ in range(5):
        await limiter.acquire()

    await limiter.acquire()

    assert timer.sleeps == [pytest.approx(1.0)]


async def test_holds_the_average_rate_over_a_long_run() -> None:
    timer = FakeTimer()
    limiter = TokenBucketLimiter(RateLimit(rate=20, period=60.0, burst=20), timer)

    for _ in range(20 + 40):
        await limiter.acquire()

    assert timer.now == pytest.approx(120.0)


async def test_refills_while_idle_up_to_the_burst() -> None:
    timer = FakeTimer()
    limiter = TokenBucketLimiter(ONE_PER_SECOND_BURST_FIVE, timer)
    for _ in range(5):
        await limiter.acquire()

    timer.now += 3
    assert limiter.tokens == pytest.approx(3.0)
    timer.now += 100
    assert limiter.tokens == pytest.approx(5.0)


async def test_concurrent_acquires_share_the_bucket() -> None:
    timer = FakeTimer()
    limiter = TokenBucketLimiter(ONE_PER_SECOND_BURST_FIVE, timer)

    await asyncio.gather(*(limiter.acquire() for _ in range(7)))

    assert timer.now == pytest.approx(2.0)
