from collections.abc import AsyncIterator

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import Provider, Scope, from_context, provide
from redis.asyncio import Redis

from app.clients import LoginThrottle, RedisLoginThrottle
from app.config import ApiSettings, AuthSettings, BotSettings, DatabaseSettings, RedisSettings, Settings
from app.utils import Clock, SystemClock


class SettingsProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings)

    @provide
    def database(self, settings: Settings) -> DatabaseSettings:
        return settings.db

    @provide
    def redis(self, settings: Settings) -> RedisSettings:
        return settings.redis

    @provide
    def bot(self, settings: Settings) -> BotSettings:
        return settings.bot

    @provide
    def api(self, settings: Settings) -> ApiSettings:
        return settings.api

    @provide
    def auth(self, settings: Settings) -> AuthSettings:
        return settings.auth


class InfraProvider(Provider):
    scope = Scope.APP

    clock = provide(SystemClock, provides=Clock)
    login_throttle = provide(RedisLoginThrottle, provides=LoginThrottle)

    @provide
    async def bot(self, settings: BotSettings) -> AsyncIterator[Bot]:
        bot = Bot(settings.token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        yield bot
        await bot.session.close()

    @provide
    async def redis(self, settings: RedisSettings) -> AsyncIterator[Redis]:
        redis = Redis(
            host=settings.host,
            port=settings.port,
            password=settings.password.get_secret_value(),
            db=settings.db,
        )
        yield redis
        await redis.aclose()
