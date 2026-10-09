from functools import partial

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from dishka import AsyncContainer
from dishka.integrations.aiogram import setup_dishka
from redis.asyncio import Redis

from bot.handlers import create_router
from bot.middlewares import ErrorsMiddleware
from bot.startup import sync_command_menus


def create_dispatcher(container: AsyncContainer, redis: Redis) -> Dispatcher:
    dp = Dispatcher(storage=RedisStorage(redis))
    errors = ErrorsMiddleware()
    dp.message.outer_middleware(errors)
    dp.callback_query.outer_middleware(errors)
    dp.include_router(create_router())
    setup_dishka(container, router=dp, auto_inject=True)
    dp.startup.register(partial(sync_command_menus, container))
    return dp
