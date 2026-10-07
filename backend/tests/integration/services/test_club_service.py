import pytest

from app.exceptions import ClubNotFoundError, ClubTitleTakenError
from app.schemas import ClubCreate, ClubUpdate, PageParams
from app.services import ClubService
from tests.factories import make_club


@pytest.fixture
async def service(request_container) -> ClubService:
    return await request_container.get(ClubService)


async def test_create_and_get(service) -> None:
    created = await service.create(ClubCreate(title=" Клуб 110 ", chat_id=-100123, sheet_name="Состав"))

    fetched = await service.get(created.id)

    assert fetched.title == "Клуб 110"
    assert fetched.chat_id == -100123
    assert fetched.is_active


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


async def test_unknown_club(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.get(999_999)


async def test_list_puts_active_first(service, db_session) -> None:
    await make_club(db_session, title="А архив", is_active=False)
    await make_club(db_session, title="Б текущий")

    page = await service.list_page(PageParams())

    assert [club.title for club in page.items] == ["Б текущий", "А архив"]
    assert page.total == 2
