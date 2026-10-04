from aiogram import Router

from bot.handlers import start


def create_router() -> Router:
    router = Router(name="root")
    router.include_routers(start.router)
    return router
