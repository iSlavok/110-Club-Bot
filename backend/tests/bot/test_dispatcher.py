from unittest.mock import AsyncMock

from dishka.integrations.aiogram import ContainerMiddleware
from redis.asyncio import Redis

from bot import create_dispatcher
from bot.middlewares import ErrorsMiddleware


async def test_errors_wrap_the_container_scope(container) -> None:
    dispatcher = create_dispatcher(container, AsyncMock(spec=Redis))

    # A handled domain error must leave the request scope as an exception, so the session rolls back.
    for observer in (dispatcher.message, dispatcher.callback_query):
        assert [type(m) for m in observer.outer_middleware._middlewares] == [ErrorsMiddleware, ContainerMiddleware]
