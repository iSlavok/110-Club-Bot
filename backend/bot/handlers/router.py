from aiogram import Router

from bot.handlers import (
    admin_commands,
    bot_blocking,
    chat_join_requests,
    chat_service_messages,
    kick_approvals,
    removal_requests,
    schedule,
    start,
    student_status,
    vk_link,
    vk_lookup,
)


def create_router() -> Router:
    router = Router(name="root")
    router.include_routers(
        start.router,
        admin_commands.router,
        bot_blocking.router,
        vk_link.router,
        vk_lookup.router,
        student_status.router,
        schedule.router,
        removal_requests.router,
        kick_approvals.router,
        chat_join_requests.router,
        chat_service_messages.router,
    )
    return router
