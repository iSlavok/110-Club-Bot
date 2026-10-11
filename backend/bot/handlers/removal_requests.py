from aiogram import Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.schemas import TelegramProfile
from app.services import MembershipRemovalService
from app.telegram import RemovalRequestCallback

router = Router(name="removal_requests")


@router.callback_query(RemovalRequestCallback.filter())
async def decide_removal(
    callback: CallbackQuery,
    callback_data: RemovalRequestCallback,
    membership_removal_service: FromDishka[MembershipRemovalService],
) -> None:
    decider = TelegramProfile(
        tg_id=callback.from_user.id,
        tg_username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )
    status = await membership_removal_service.decide(callback_data.request_id, callback_data.decision, decider)
    await callback.answer(texts.alerts.removal_decided(status))
