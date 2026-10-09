from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from app.services import BotAdminService


# The command menu is only a hint: anyone can type an admin command, so every one of them is behind this filter.
@inject
async def is_admin(message: Message, bot_admin_service: FromDishka[BotAdminService]) -> bool:
    if message.from_user is None:
        return False
    return await bot_admin_service.is_admin(message.from_user.id)
