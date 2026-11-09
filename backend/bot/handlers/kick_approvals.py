from aiogram import Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.schemas import TelegramProfile
from app.services import ChatAccessService
from app.telegram import KickApprovalCallback

router = Router(name="kick_approvals")


@router.callback_query(KickApprovalCallback.filter())
async def approve_kicks(
    callback: CallbackQuery,
    callback_data: KickApprovalCallback,
    chat_access_service: FromDishka[ChatAccessService],
) -> None:
    decider = TelegramProfile(
        tg_id=callback.from_user.id,
        tg_username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )
    await chat_access_service.approve_kicks(callback_data.block_id, decider)
    await callback.answer(texts.alerts.KICKS_APPROVED_ANSWER)
