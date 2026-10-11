from aiogram.fsm.state import State, StatesGroup


class VkLinkStates(StatesGroup):
    waiting_for_profile = State()
