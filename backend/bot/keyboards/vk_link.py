from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app import texts
from app.schemas import VkCandidate
from bot.callbacks import VkLinkAction, VkLinkCallback


def confirm_keyboard(candidate: VkCandidate) -> InlineKeyboardMarkup:
    confirm = VkLinkCallback(action=VkLinkAction.CONFIRM, vk_id=candidate.vk_id)
    cancel = VkLinkCallback(action=VkLinkAction.CANCEL, vk_id=candidate.vk_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.vk_link.confirm_button(candidate), callback_data=confirm.pack())],
            [InlineKeyboardButton(text=texts.vk_link.CANCEL_BUTTON, callback_data=cancel.pack())],
        ],
    )


def oauth_keyboard(authorize_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=texts.vk_link.OAUTH_BUTTON, url=authorize_url)]],
    )
