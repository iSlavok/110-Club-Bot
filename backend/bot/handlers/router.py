from aiogram import Router

from bot.handlers import admin_commands, start


def create_router() -> Router:
    router = Router(name="root")
    router.include_routers(start.router, admin_commands.router)
    return router
