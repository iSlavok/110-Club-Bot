from datetime import UTC, datetime
from unittest.mock import AsyncMock

from aiogram import Bot
from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import Clock
from tests.fakes import FrozenClock

DEFAULT_NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


class TestDatabaseProvider(Provider):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self._session = session

    @provide(scope=Scope.REQUEST)
    def session(self) -> AsyncSession:
        return self._session


class TestInfraProvider(Provider):
    scope = Scope.APP

    @provide
    def clock(self) -> Clock:
        return FrozenClock(DEFAULT_NOW)

    @provide
    def bot(self) -> Bot:
        return AsyncMock(spec=Bot)

    @provide
    def redis(self) -> Redis:
        redis = AsyncMock(spec=Redis)
        # redis-py declares ping() as a plain method returning an awaitable, so spec alone yields a sync mock.
        redis.ping = AsyncMock(return_value=True)
        return redis
