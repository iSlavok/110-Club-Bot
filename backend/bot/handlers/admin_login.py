from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app.schemas import TelegramProfile
from app.services import LoginService
from bot import texts

router = Router(name="admin_login")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(Command("login"))
async def login(message: Message, login_service: FromDishka[LoginService]) -> None:
    if message.from_user is None:
        return
    profile = TelegramProfile(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    issued = await login_service.issue_code(profile)
    await message.answer(texts.auth.login_code(issued))
