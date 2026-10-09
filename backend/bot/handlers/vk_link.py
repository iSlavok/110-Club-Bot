from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from app import texts
from app.schemas import VkAlreadyLinked, VkLinkByOAuth, VkLinkByProfile, VkLinkUnavailable
from app.services import VkLinkService
from bot import keyboards
from bot.callbacks import VkLinkAction, VkLinkCallback
from bot.states import VkLinkStates

CANDIDATE_KEY = "vk_candidate_id"

router = Router(name="vk_link")
router.message.filter(F.chat.type == ChatType.PRIVATE)


async def offer_vk_link(message: Message, state: FSMContext, tg_id: int, vk_link_service: VkLinkService) -> None:
    offer = await vk_link_service.offer(tg_id)
    await state.clear()
    match offer:
        case VkAlreadyLinked():
            await message.answer(texts.vk_link.already_linked(offer))
        case VkLinkByProfile():
            await state.set_state(VkLinkStates.waiting_for_profile)
            await message.answer(texts.vk_link.ASK_PROFILE_LINK)
        case VkLinkByOAuth():
            await message.answer(texts.vk_link.OAUTH_OFFER, reply_markup=keyboards.oauth_keyboard(offer.authorize_url))
        case VkLinkUnavailable():
            await message.answer(texts.vk_link.UNAVAILABLE)


@router.message(Command("vk"))
async def vk(message: Message, state: FSMContext, vk_link_service: FromDishka[VkLinkService]) -> None:
    if message.from_user is None:
        return
    await offer_vk_link(message, state, message.from_user.id, vk_link_service)


@router.message(VkLinkStates.waiting_for_profile, F.text, ~F.text.startswith("/"))
async def receive_profile_link(
    message: Message,
    state: FSMContext,
    vk_link_service: FromDishka[VkLinkService],
) -> None:
    if message.from_user is None or message.text is None:
        return
    candidate = await vk_link_service.find_candidate(message.from_user.id, message.text)
    await state.update_data({CANDIDATE_KEY: candidate.vk_id})
    await message.answer(
        texts.vk_link.confirm_candidate(candidate),
        reply_markup=keyboards.confirm_keyboard(candidate),
    )


@router.callback_query(VkLinkCallback.filter(F.action == VkLinkAction.CONFIRM))
async def confirm_profile(
    callback: CallbackQuery,
    callback_data: VkLinkCallback,
    state: FSMContext,
    vk_link_service: FromDishka[VkLinkService],
) -> None:
    if not await _is_current_candidate(state, callback_data):
        await callback.answer(texts.vk_link.STALE_CONFIRMATION, show_alert=True)
        return
    result = await vk_link_service.confirm_candidate(callback.from_user.id, callback_data.vk_id)
    await state.clear()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(texts.vk_link.linked(result))


@router.callback_query(VkLinkCallback.filter(F.action == VkLinkAction.CANCEL))
async def cancel_profile(callback: CallbackQuery, callback_data: VkLinkCallback, state: FSMContext) -> None:
    if not await _is_current_candidate(state, callback_data):
        await callback.answer(texts.vk_link.STALE_CONFIRMATION, show_alert=True)
        return
    await state.update_data({CANDIDATE_KEY: None})
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(texts.vk_link.CANCELLED)


async def _is_current_candidate(state: FSMContext, callback_data: VkLinkCallback) -> bool:
    if await state.get_state() != VkLinkStates.waiting_for_profile.state:
        return False
    data = await state.get_data()
    return data.get(CANDIDATE_KEY) == callback_data.vk_id
