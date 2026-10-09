from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class VkLinkAction(StrEnum):
    CONFIRM = "confirm"
    CANCEL = "cancel"


# vk_id ties the button to the profile it shows: an older confirmation must not link a newer candidate.
class VkLinkCallback(CallbackData, prefix="vk"):
    action: VkLinkAction
    vk_id: int
