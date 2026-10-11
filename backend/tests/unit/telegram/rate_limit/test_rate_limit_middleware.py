from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import DeleteMessage, GetMe, SendMessage, TelegramMethod

from app.telegram.rate_limit import RELAXED_METHODS, SEND_METHODS, RateLimitMiddleware
from tests.fakes import FakeTimer

PRIVATE_CHAT = 42
GROUP_CHAT = -100500


def _send(chat_id: int | str = PRIVATE_CHAT) -> SendMessage:
    return SendMessage(chat_id=chat_id, text="hi")


def _delete(chat_id: int = PRIVATE_CHAT) -> DeleteMessage:
    return DeleteMessage(chat_id=chat_id, message_id=1)


def _retry_after(seconds: int = 10) -> TelegramRetryAfter:
    return TelegramRetryAfter(method=_send(), message="Too Many Requests", retry_after=seconds)


@pytest.fixture
def timer() -> FakeTimer:
    return FakeTimer()


@pytest.fixture
def middleware(timer: FakeTimer) -> RateLimitMiddleware:
    return RateLimitMiddleware(timer)


@pytest.fixture
def make_request() -> AsyncMock:
    return AsyncMock(return_value="ok")


async def _call(
    middleware: RateLimitMiddleware,
    make_request: AsyncMock,
    method: TelegramMethod[Any],
    times: int = 1,
) -> None:
    for _ in range(times):
        await middleware(make_request, AsyncMock(spec=Bot), method)


def test_method_sets_do_not_overlap() -> None:
    assert not SEND_METHODS & RELAXED_METHODS


@pytest.mark.parametrize("method", sorted(SEND_METHODS | RELAXED_METHODS, key=str))
def test_every_limited_method_targets_a_chat(method: type[TelegramMethod[Any]]) -> None:
    assert "chat_id" in method.model_fields


async def test_returns_the_response(middleware, make_request) -> None:
    response = await middleware(make_request, AsyncMock(spec=Bot), _send())

    assert response == "ok"
    make_request.assert_awaited_once()


async def test_private_chat_gets_a_burst_then_one_message_per_second(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, _send(), times=5)
    assert timer.now == 0

    await _call(middleware, make_request, _send())

    assert timer.now == pytest.approx(1.0)


async def test_group_gets_twenty_messages_per_minute(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, _send(GROUP_CHAT), times=20)
    assert timer.now < 1

    await _call(middleware, make_request, _send(GROUP_CHAT))

    assert timer.now == pytest.approx(3.0)


async def test_edits_and_deletes_have_a_looser_bucket_of_their_own(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, _send(), times=5)

    await _call(middleware, make_request, _delete(), times=25)

    assert timer.now == pytest.approx(1.0)  # 30 requests at the global 25/s; the send bucket alone would take 25 s


async def test_numeric_string_chat_id_is_limited_per_chat(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, _send(str(PRIVATE_CHAT)), times=6)

    assert timer.now == pytest.approx(1.0)


async def test_username_chat_id_is_limited_only_globally(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, _send("@club_channel"), times=6)

    assert timer.now < 0.1


async def test_methods_without_chat_share_the_global_limit(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, GetMe(), times=30)

    assert timer.now == pytest.approx(1.0)


async def test_retry_after_pauses_and_retries(middleware, make_request, timer) -> None:
    make_request.side_effect = [_retry_after(10), "ok"]

    response = await middleware(make_request, AsyncMock(spec=Bot), _send())

    assert response == "ok"
    assert make_request.await_count == 2
    assert timer.now == pytest.approx(10.5)


async def test_gives_up_after_three_attempts(middleware, make_request) -> None:
    make_request.side_effect = _retry_after(10)

    with pytest.raises(TelegramRetryAfter):
        await middleware(make_request, AsyncMock(spec=Bot), _send())

    assert make_request.await_count == 3


async def test_retry_after_pauses_requests_to_other_chats(middleware, make_request, timer) -> None:
    make_request.side_effect = _retry_after(10)
    with pytest.raises(TelegramRetryAfter):
        await middleware(make_request, AsyncMock(spec=Bot), _send())
    failed_at = timer.now
    make_request.side_effect = None

    await _call(middleware, make_request, _send(GROUP_CHAT))

    assert timer.now == pytest.approx(failed_at + 10.5)


async def test_cleanup_drops_idle_chat_limiters(middleware, make_request, timer) -> None:
    await _call(middleware, make_request, _send())
    await _call(middleware, make_request, _delete())
    timer.now += 301

    assert middleware.cleanup_expired() == 2
    assert middleware.cleanup_expired() == 0
