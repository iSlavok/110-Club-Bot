from app.models import User
from app.schemas import TelegramProfile
from app.services import UserService


async def test_register_persists_and_returns_schema(request_container, db_session) -> None:
    service = await request_container.get(UserService)

    result = await service.register(TelegramProfile(tg_id=10, tg_username=None, full_name="Аня Смирнова"))

    stored = await db_session.get(User, result.id)
    assert stored is not None
    assert stored.tg_id == 10
    assert result.full_name == "Аня Смирнова"
    assert result.vk_id is None
