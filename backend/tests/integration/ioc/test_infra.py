from aiogram import Bot
from pydantic import SecretStr

from app.config import BotSettings, DatabaseSettings, RedisSettings, Settings
from app.ioc import create_container
from app.telegram import RateLimitMiddleware
from tests.providers import BOT_TOKEN


async def test_every_bot_call_goes_through_the_rate_limiter() -> None:
    settings = Settings(
        db=DatabaseSettings(name="unused", user="unused", password=SecretStr("unused")),
        redis=RedisSettings(password=SecretStr("unused")),
        bot=BotSettings(token=SecretStr(BOT_TOKEN)),
    )
    container = create_container(settings)
    try:
        bot = await container.get(Bot)
        rate_limit = await container.get(RateLimitMiddleware)
    finally:
        await container.close()

    assert rate_limit in bot.session.middleware._middlewares
