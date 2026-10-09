from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InlineKeyboardMarkup, Message
from sqlalchemy import select

from app import texts
from app.enums import VkLinkMode
from app.exceptions import UserNotRegisteredError, VkProfileNotFoundError
from app.models import User
from app.services import VkLinkService
from bot.callbacks import VkLinkAction, VkLinkCallback
from bot.handlers.vk_link import cancel_profile, confirm_profile, receive_profile_link, vk
from bot.states import VkLinkStates
from tests.factories import make_block, make_club, make_membership, make_user, set_app_settings

TG_ID = 42
VK_ID = 4242


def _message(text: str = "/vk") -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=TG_ID, username="kate", full_name="Катя Орлова")
    message.text = text
    return message


def _callback(action: VkLinkAction, vk_id: int = VK_ID) -> tuple[AsyncMock, VkLinkCallback]:
    callback = AsyncMock()
    callback.from_user = MagicMock(id=TG_ID)
    callback.message = AsyncMock(spec=Message)
    # aiogram's edit_text returns an awaitable method object, so spec alone yields a sync mock.
    callback.message.edit_text = AsyncMock()
    return callback, VkLinkCallback(action=action, vk_id=vk_id)


@pytest.fixture
async def service(request_container) -> VkLinkService:
    return await request_container.get(VkLinkService)


@pytest.fixture
async def link_mode(db_session, vk) -> None:
    await set_app_settings(db_session, vk_link_mode=VkLinkMode.LINK)
    vk.add_user(VK_ID, "Катя", "Орлова", screen_name="kate.orlova")


@pytest.mark.usefixtures("link_mode")
async def test_vk_command_asks_for_link(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    message = _message()

    await vk(message, state, service)

    assert await state.get_state() == VkLinkStates.waiting_for_profile.state
    message.answer.assert_awaited_once_with(texts.vk_link.ASK_PROFILE_LINK)


@pytest.mark.usefixtures("link_mode")
async def test_vk_command_does_not_register(service, state, db_session) -> None:
    message = _message()

    with pytest.raises(UserNotRegisteredError) as error:
        await vk(message, state, service)

    assert texts.errors.for_error(error.value) == "Сначала нажми /start."
    assert await db_session.scalar(select(User).where(User.tg_id == TG_ID)) is None
    assert await state.get_state() is None


async def test_vk_command_shows_status_when_already_linked(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID, vk_id=VK_ID)
    block = await make_block(db_session, await make_club(db_session, title="Химия"), title="Блок 5")
    await make_membership(db_session, block, vk_id=VK_ID)
    await state.set_state(VkLinkStates.waiting_for_profile)
    message = _message()

    await vk(message, state, service)

    text = message.answer.await_args.args[0]
    assert f"vk.com/id{VK_ID}" in text
    assert "Изменить привязку нельзя" in text
    assert "Ты в клубе Химия, блок Блок 5." in text
    assert await state.get_state() is None


@pytest.mark.usefixtures("link_mode")
async def test_profile_link_gets_confirmation_buttons(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    await state.set_state(VkLinkStates.waiting_for_profile)
    message = _message("https://vk.com/kate.orlova")

    await receive_profile_link(message, state, service)

    text = message.answer.await_args.args[0]
    keyboard: InlineKeyboardMarkup = message.answer.await_args.kwargs["reply_markup"]
    assert "Катя Орлова" in text
    assert keyboard.inline_keyboard[0][0].text == "Это я: Катя Орлова"
    assert keyboard.inline_keyboard[0][0].callback_data == f"vk:confirm:{VK_ID}"
    assert keyboard.inline_keyboard[1][0].callback_data == f"vk:cancel:{VK_ID}"
    db_user = await db_session.scalar(select(User).where(User.tg_id == TG_ID))
    assert db_user.vk_id is None


@pytest.mark.usefixtures("link_mode")
async def test_unknown_profile_keeps_waiting_for_a_link(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    await state.set_state(VkLinkStates.waiting_for_profile)

    with pytest.raises(VkProfileNotFoundError) as error:
        await receive_profile_link(_message("vk.com/nobody"), state, service)

    assert texts.errors.for_error(error.value).startswith("Не нашёл такую личную страницу VK.")
    assert await state.get_state() == VkLinkStates.waiting_for_profile.state


@pytest.mark.usefixtures("link_mode")
async def test_confirmation_links_vk(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    await state.set_state(VkLinkStates.waiting_for_profile)
    await receive_profile_link(_message("vk.com/kate.orlova"), state, service)
    callback, data = _callback(VkLinkAction.CONFIRM)

    await confirm_profile(callback, data, state, service)

    db_user = await db_session.scalar(select(User).where(User.tg_id == TG_ID))
    assert db_user.vk_id == VK_ID
    text = callback.message.edit_text.await_args.args[0]
    assert text.startswith(texts.vk_link.LINKED)
    assert "В текущем блоке тебя нет в списках" in text
    assert await state.get_state() is None


@pytest.mark.usefixtures("link_mode")
async def test_button_of_an_older_candidate_is_stale(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    await state.set_state(VkLinkStates.waiting_for_profile)
    await receive_profile_link(_message("vk.com/kate.orlova"), state, service)
    callback, data = _callback(VkLinkAction.CONFIRM, vk_id=1)

    await confirm_profile(callback, data, state, service)

    callback.answer.assert_awaited_once_with(texts.vk_link.STALE_CONFIRMATION, show_alert=True)
    db_user = await db_session.scalar(select(User).where(User.tg_id == TG_ID))
    assert db_user.vk_id is None


@pytest.mark.usefixtures("link_mode")
async def test_cancel_asks_for_another_link(service, state, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    await state.set_state(VkLinkStates.waiting_for_profile)
    await receive_profile_link(_message("vk.com/kate.orlova"), state, service)
    callback, data = _callback(VkLinkAction.CANCEL)

    await cancel_profile(callback, data, state)

    callback.message.edit_text.assert_awaited_once_with(texts.vk_link.CANCELLED)
    assert await state.get_state() == VkLinkStates.waiting_for_profile.state
    confirm, confirm_data = _callback(VkLinkAction.CONFIRM)
    await confirm_profile(confirm, confirm_data, state, service)
    confirm.answer.assert_awaited_once_with(texts.vk_link.STALE_CONFIRMATION, show_alert=True)
