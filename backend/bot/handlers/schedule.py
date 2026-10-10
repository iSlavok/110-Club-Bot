from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.services import ScheduleService

router = Router(name="schedule")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(Command("schedule"))
async def schedule(message: Message, schedule_service: FromDishka[ScheduleService]) -> None:
    if message.from_user is None:
        return
    schedules = await schedule_service.build(message.from_user.id)
    await message.answer(texts.schedule.schedule(schedules))
