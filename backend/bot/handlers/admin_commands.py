from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.config import PublicSettings
from app.schemas import TelegramProfile
from app.services import LoginService, StatusService
from bot.filters import is_admin

router = Router(name="admin_commands")
# A non-admin's message falls through unhandled, like any unknown command.
router.message.filter(F.chat.type == ChatType.PRIVATE, is_admin)


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


@router.message(Command("adminka"))
async def adminka(message: Message, settings: FromDishka[PublicSettings]) -> None:
    await message.answer(texts.auth.admin_panel_link(settings.url))


@router.message(Command("status"))
async def status(message: Message, status_service: FromDishka[StatusService]) -> None:
    report = await status_service.build()
    await message.answer(texts.status.status_report(report))
