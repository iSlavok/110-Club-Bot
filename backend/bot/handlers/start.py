from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.schemas import TelegramProfile
from app.services import BotAdminService, StudentStatusService, UserService, VkLinkService
from bot.handlers.student_status import answer_student_status
from bot.handlers.vk_link import offer_vk_link

router = Router(name="start")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
async def start(
    message: Message,
    *,
    state: FSMContext,
    user_service: FromDishka[UserService],
    bot_admin_service: FromDishka[BotAdminService],
    vk_link_service: FromDishka[VkLinkService],
    student_status_service: FromDishka[StudentStatusService],
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
    # A linked student comes back for the chat, often after unblocking the bot: the status carries the join link.
    if user.vk_id is not None:
        await state.clear()
        await answer_student_status(message, user.tg_id, student_status_service)
        return
    await message.answer(texts.common.greeting(user))
    await offer_vk_link(message, state, user.tg_id, vk_link_service)
