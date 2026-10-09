from aiogram import Router

from bot.handlers import admin_commands, removal_requests, start, vk_link


def create_router() -> Router:
    router = Router(name="root")
    router.include_routers(start.router, admin_commands.router, vk_link.router, removal_requests.router)
    return router
