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
