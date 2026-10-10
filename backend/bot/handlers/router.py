from aiogram import Router

from bot.handlers import (
    admin_commands,
    chat_join_requests,
    chat_service_messages,
    removal_requests,
    start,
    student_status,
    vk_link,
)


def create_router() -> Router:
    router = Router(name="root")
    router.include_routers(
        start.router,
        admin_commands.router,
        vk_link.router,
        student_status.router,
        removal_requests.router,
        chat_join_requests.router,
        chat_service_messages.router,
    )
    return router
