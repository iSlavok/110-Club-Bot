from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import EphemeralMessageParameters, LinkPreviewOptions, Message, User
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.enums import Permission
from app.services import BotAdminService, UserService
from bot.filters import is_admin

router = Router(name="vk_lookup")
# A non-admin's command falls through unhandled: the bot stays silent in the club chat.
router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), is_admin)


@router.message(Command("vk"))
async def vk_lookup(
    message: Message,
    bot_admin_service: FromDishka[BotAdminService],
    user_service: FromDishka[UserService],
) -> None:
    if message.from_user is None:
        return
    student = _replied_student(message)
    if not await bot_admin_service.has_permission(message.from_user.id, Permission.USERS_VIEW):
        text = texts.vk_lookup.NO_PERMISSION
    elif student is None:
        text = texts.vk_lookup.NO_TARGET
    else:
        user = await user_service.find_by_tg_id(student.id)
        text = texts.vk_lookup.student_vk(student.id, student.full_name, user)
    await message.answer(
        text,
        ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=message.from_user.id),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


# In a forum topic a message without a reply still points at the topic's first, service message.
def _replied_student(message: Message) -> User | None:
    reply = message.reply_to_message
    if reply is None or reply.forum_topic_created is not None:
        return None
    if reply.from_user is None or reply.from_user.is_bot:
        return None
    return reply.from_user
