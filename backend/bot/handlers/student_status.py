from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.services import StudentStatusService
from app.telegram import chat_invite_keyboard

router = Router(name="student_status")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(Command("status"))
async def status(message: Message, student_status_service: FromDishka[StudentStatusService]) -> None:
    if message.from_user is None:
        return
    report = await student_status_service.build(message.from_user.id)
    keyboard = chat_invite_keyboard([club.access for club in report.clubs])
    await message.answer(texts.student_status.student_status(report), reply_markup=keyboard)
