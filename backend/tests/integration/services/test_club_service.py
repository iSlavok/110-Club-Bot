import pytest
from aiogram.types import BotCommandScopeChatMember

from app.exceptions import ClubNotFoundError, ClubTitleTakenError
from app.schemas import ClubCreate, ClubUpdate, PageParams
from app.services import ClubService
from app.telegram import CHAT_ADMIN_COMMANDS
from tests.factories import make_club
from tests.providers import OWNER_TG_ID


@pytest.fixture
async def service(request_container) -> ClubService:
    return await request_container.get(ClubService)


async def test_create_and_get(service) -> None:
    created = await service.create(ClubCreate(title=" Клуб 110 ", chat_id=-100123, sheet_name="Состав"))

    fetched = await service.get(created.id)

    assert fetched.title == "Клуб 110"
    assert fetched.chat_id == -100123
    assert fetched.is_active
    assert not fetched.hide_service_messages


async def test_titles_are_unique(service, db_session) -> None:
    await make_club(db_session, title="Клуб 110")

    with pytest.raises(ClubTitleTakenError):
        await service.create(ClubCreate(title="Клуб 110"))


async def test_update_clears_nullable_and_keeps_omitted(service, db_session) -> None:
    club = await make_club(db_session, chat_id=-1, sheet_name="Состав")

    updated = await service.update(club.id, ClubUpdate.model_validate({"chat_id": None, "is_active": False}))

    assert updated.chat_id is None
    assert updated.sheet_name == "Состав"
    assert not updated.is_active


async def test_update_turns_on_hiding_service_messages(service, db_session) -> None:
    club = await make_club(db_session)

    updated = await service.update(club.id, ClubUpdate.model_validate({"hide_service_messages": True}))

    assert updated.hide_service_messages


@pytest.mark.parametrize(("chat_id", "link"), [(-1, "https://t.me/+club"), (-2, None)])
async def test_join_link_is_dropped_only_when_the_chat_changes(service, db_session, chat_id, link) -> None:
    club = await make_club(db_session, chat_id=-1, chat_invite_link="https://t.me/+club")

    updated = await service.update(club.id, ClubUpdate.model_validate({"chat_id": chat_id}))

    assert updated.chat_invite_link == link


async def test_unknown_club(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.get(999_999)


async def test_list_puts_active_first(service, db_session) -> None:
    await make_club(db_session, title="А архив", is_active=False)
    await make_club(db_session, title="Б текущий")

    page = await service.list_page(PageParams())

    assert [club.title for club in page.items] == ["Б текущий", "А архив"]
    assert page.total == 2


def _chat_menu_scopes(bot) -> list[BotCommandScopeChatMember]:
    calls = bot.set_my_commands.await_args_list
    return [call.kwargs["scope"] for call in calls if call.args == (list(CHAT_ADMIN_COMMANDS),)]


async def test_create_with_a_chat_shows_admins_the_chat_menu(service, bot) -> None:
    await service.create(ClubCreate(title="Клуб 110", chat_id=-100))
    await service.create(ClubCreate(title="Без чата"))

    assert _chat_menu_scopes(bot) == [BotCommandScopeChatMember(chat_id=-100, user_id=OWNER_TG_ID)]


@pytest.mark.parametrize(
    "case",
    [
        ({"chat_id": -1}, {"chat_id": -2}, -2),
        ({"chat_id": -1, "is_active": False}, {"is_active": True}, -1),
        ({}, {"chat_id": -3}, -3),
    ],
    ids=["chat changed", "club turned on", "chat set"],
)
async def test_update_shows_the_chat_menu_when_a_chat_becomes_reachable(service, bot, db_session, case) -> None:
    club_fields, patch, chat_id = case
    club = await make_club(db_session, **club_fields)

    await service.update(club.id, ClubUpdate.model_validate(patch))

    assert _chat_menu_scopes(bot) == [BotCommandScopeChatMember(chat_id=chat_id, user_id=OWNER_TG_ID)]


@pytest.mark.parametrize("patch", [{"title": "Новое имя"}, {"is_active": False}, {"chat_id": None}])
async def test_update_leaves_the_chat_menu_otherwise(service, bot, db_session, patch) -> None:
    club = await make_club(db_session, chat_id=-1)

    await service.update(club.id, ClubUpdate.model_validate(patch))

    assert _chat_menu_scopes(bot) == []
