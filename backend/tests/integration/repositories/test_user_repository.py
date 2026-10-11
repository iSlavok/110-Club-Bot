import pytest

from app.repositories import UserRepository
from tests.factories import make_user


async def test_upsert_creates_user(db_session) -> None:
    repository = UserRepository(db_session)

    user = await repository.upsert_by_tg_id(tg_id=1, tg_username="ivan", full_name="Иван Иванов")

    assert user.id is not None
    assert (await repository.get_by_tg_id(1)) is user


async def test_upsert_refreshes_loaded_user_and_keeps_vk(db_session) -> None:
    existing = await make_user(db_session, tg_id=2, tg_username="old", vk_id=555)
    repository = UserRepository(db_session)

    user = await repository.upsert_by_tg_id(tg_id=2, tg_username="new", full_name="Пётр Петров")

    assert user is existing
    assert user.tg_username == "new"
    assert user.full_name == "Пётр Петров"
    assert user.vk_id == 555


async def test_search_matches_name_username_and_ids(db_session) -> None:
    anna = await make_user(db_session, full_name="Анна Белова", tg_username="anna_b", tg_id=111, vk_id=222)
    await make_user(db_session, full_name="Борис", tg_username="boris")
    repository = UserRepository(db_session)

    by_name = await repository.search_page(query="белов", limit=10, offset=0)
    by_username = await repository.search_page(query="ANNA_", limit=10, offset=0)
    by_vk = await repository.search_page(query="222", limit=10, offset=0)

    assert by_name.items == [anna]
    assert by_username.items == [anna]
    assert by_vk.items == [anna]


async def test_total_counts_every_match_not_only_the_page(db_session) -> None:
    await make_user(db_session, full_name="Анна Белова")
    await make_user(db_session, full_name="Анна Котова")
    await make_user(db_session, full_name="Борис")
    repository = UserRepository(db_session)

    page = await repository.search_page(query="анна", limit=1, offset=0)

    assert len(page.items) == 1
    assert page.total == 2


async def test_search_treats_wildcards_literally(db_session) -> None:
    await make_user(db_session, full_name="Ivan", tg_username="ivan")
    repository = UserRepository(db_session)

    assert (await repository.search_page(query="%", limit=10, offset=0)).total == 0
    assert (await repository.search_page(query="_", limit=10, offset=0)).total == 0


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("белава", "Анна Белова"),
        ("Белова Анна", "Анна Белова"),
        ("  АННА   белова ", "Анна Белова"),
        ("алёна", "Алена Смирнова"),
        ("смирнова алена", "Алена Смирнова"),
    ],
)
async def test_fuzzy_search_survives_typos_word_order_and_yo(db_session, query, expected) -> None:
    await make_user(db_session, full_name="Анна Белова", tg_username=None)
    await make_user(db_session, full_name="Алена Смирнова", tg_username=None)
    await make_user(db_session, full_name="Борис Котов", tg_username="boris")
    repository = UserRepository(db_session)

    found = await repository.search_page(query=query, limit=10, offset=0)

    assert [user.full_name for user in found.items][:1] == [expected]
    assert "Борис Котов" not in [user.full_name for user in found.items]


async def test_closest_match_comes_first(db_session) -> None:
    await make_user(db_session, full_name="Иван Белоусов", tg_username=None)
    exact = await make_user(db_session, full_name="Пётр Белов", tg_username=None)
    repository = UserRepository(db_session)

    found = await repository.search_page(query="белов", limit=10, offset=0)

    assert found.items[0] is exact
