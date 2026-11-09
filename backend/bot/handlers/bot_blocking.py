from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated
from dishka.integrations.aiogram import FromDishka

from app.services import UserService

router = Router(name="bot_blocking")


@router.my_chat_member(F.chat.type == ChatType.PRIVATE)
async def bot_status_changed(update: ChatMemberUpdated, user_service: FromDishka[UserService]) -> None:
    blocked = update.new_chat_member.status == ChatMemberStatus.KICKED
    await user_service.set_bot_blocked(update.from_user.id, blocked=blocked)
