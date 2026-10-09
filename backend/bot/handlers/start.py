from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.schemas import TelegramProfile
from app.services import BotAdminService, UserService

router = Router(name="start")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
async def start(
    message: Message,
    user_service: FromDishka[UserService],
    bot_admin_service: FromDishka[BotAdminService],
) -> None:
    if message.from_user is None:
        return
    profile = TelegramProfile(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    user = await user_service.register(profile)
    await bot_admin_service.sync_command_menu(profile.tg_id)
    await message.answer(texts.common.greeting(user))
