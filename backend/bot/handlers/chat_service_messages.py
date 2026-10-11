from aiogram import F, Router
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app.services import ChatAccessService

router = Router(name="chat_service_messages")


@router.message(F.new_chat_members | F.left_chat_member)
async def hide_service_message(message: Message, chat_access_service: FromDishka[ChatAccessService]) -> None:
    await chat_access_service.hide_service_message(chat_id=message.chat.id, message_id=message.message_id)
