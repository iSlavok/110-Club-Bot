from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app import texts
from app.enums import RemovalDecision
from app.telegram.callbacks import RemovalRequestCallback


def removal_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    confirm = RemovalRequestCallback(request_id=request_id, decision=RemovalDecision.CONFIRM)
    reject = RemovalRequestCallback(request_id=request_id, decision=RemovalDecision.REJECT)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts.alerts.CONFIRM_REMOVAL_BUTTON, callback_data=confirm.pack()),
                InlineKeyboardButton(text=texts.alerts.REJECT_REMOVAL_BUTTON, callback_data=reject.pack()),
            ],
        ],
    )
