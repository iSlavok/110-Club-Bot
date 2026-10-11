from app.telegram.rate_limit import LimiterCache, RateLimit
from tests.fakes import FakeTimer

PRIVATE = RateLimit(rate=1, period=1.0, burst=5)
GROUP = RateLimit(rate=20, period=60.0, burst=20)


def _cache(timer: FakeTimer, max_size: int = 100) -> LimiterCache:
    return LimiterCache(private_limit=PRIVATE, group_limit=GROUP, timer=timer, max_size=max_size, ttl_seconds=300)


def test_returns_the_same_limiter_for_a_chat() -> None:
    cache = _cache(FakeTimer())

    assert cache.get(42) is cache.get(42)


def test_private_chats_and_groups_get_their_own_limits() -> None:
    cache = _cache(FakeTimer())

    assert cache.get(42).tokens == 5
    assert cache.get(-100500).tokens == 20


def test_evicts_the_least_recently_used_chat() -> None:
    cache = _cache(FakeTimer(), max_size=2)
    first = cache.get(1)
    cache.get(2)
    cache.get(1)

    cache.get(3)

    assert len(cache) == 2
    assert cache.get(1) is first


def test_cleanup_drops_only_idle_chats() -> None:
    timer = FakeTimer()
    cache = _cache(timer)
    cache.get(1)
    timer.now = 200
    active = cache.get(2)
    timer.now = 400

    removed = cache.cleanup_expired()

    assert removed == 1
    assert len(cache) == 1
    assert cache.get(2) is active
