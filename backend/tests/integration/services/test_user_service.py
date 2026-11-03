from app.models import User
from app.schemas import TelegramProfile
from app.services import UserService
from tests.factories import make_user


async def test_register_persists_and_returns_schema(request_container, db_session) -> None:
    service = await request_container.get(UserService)

    result = await service.register(TelegramProfile(tg_id=10, tg_username=None, full_name="Аня Смирнова"))

    stored = await db_session.get(User, result.id)
    assert stored is not None
    assert stored.tg_id == 10
    assert result.full_name == "Аня Смирнова"
    assert result.vk_id is None


async def test_find_by_tg_id(request_container, db_session) -> None:
    service = await request_container.get(UserService)
    user = await make_user(db_session, vk_id=5005)

    found = await service.find_by_tg_id(user.tg_id)

    assert found is not None
    assert found.vk_id == 5005
    assert await service.find_by_tg_id(1) is None
