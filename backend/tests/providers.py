from datetime import UTC, datetime
from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.types import User
from dishka import Provider, Scope, provide
from pydantic import SecretStr
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker

from app.clients import LoginThrottle
from app.config import AuthSettings, BotSettings, DatabaseSettings
from app.utils import Clock
from tests.fakes import FakeLoginThrottle, FrozenClock

DEFAULT_NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
OWNER_TG_ID = 777
BOT_TOKEN = "123456:test-token"
BOT_USERNAME = "club_test_bot"


class TestDatabaseProvider(Provider):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self._session = session

    @provide(scope=Scope.REQUEST)
    def session(self) -> AsyncSession:
        return self._session


# Lets the real DatabaseProvider commit and roll back: "commit" releases a savepoint of the test's outer transaction.
class ConnectionSessionmakerProvider(Provider):
    def __init__(self, connection: AsyncConnection) -> None:
        super().__init__()
        self._connection = connection

    # The engine factory stays in the graph and needs settings, but is never built.
    @provide(scope=Scope.APP)
    def settings(self) -> DatabaseSettings:
        return DatabaseSettings(name="unused", user="unused", password=SecretStr("unused"))

    @provide(scope=Scope.APP)
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=self._connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )


class TestInfraProvider(Provider):
    scope = Scope.APP

    @provide
    def clock(self) -> Clock:
        return FrozenClock(DEFAULT_NOW)

    @provide
    def auth_settings(self) -> AuthSettings:
        return AuthSettings(owner_ids=[OWNER_TG_ID], widget_enabled=True, cookie_secure=False)

    @provide
    def bot_settings(self) -> BotSettings:
        return BotSettings(token=SecretStr(BOT_TOKEN))

    @provide
    def login_throttle(self) -> LoginThrottle:
        return FakeLoginThrottle()

    @provide
    def bot(self) -> Bot:
        bot = AsyncMock(spec=Bot)
        bot.me.return_value = User(id=1, is_bot=True, first_name="Club", username=BOT_USERNAME)
        return bot

    @provide
    def redis(self) -> Redis:
        redis = AsyncMock(spec=Redis)
        # redis-py declares ping() as a plain method returning an awaitable, so spec alone yields a sync mock.
        redis.ping = AsyncMock(return_value=True)
        return redis
