from aiogram.filters.callback_data import CallbackData

from app.enums import RemovalDecision


class RemovalRequestCallback(CallbackData, prefix="removal"):
    request_id: int
    decision: RemovalDecision


class KickApprovalCallback(CallbackData, prefix="kicks"):
    block_id: int
