import pytest

from app.services import BotAdminService
from tests.factories import make_admin_user, make_role
from tests.providers import OWNER_TG_ID


@pytest.fixture
async def service(request_container) -> BotAdminService:
    return await request_container.get(BotAdminService)


async def test_owner_is_admin_without_an_account(service) -> None:
    assert await service.is_admin(OWNER_TG_ID)


async def test_active_admin_with_role_is_admin(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))

    assert await service.is_admin(admin.tg_id)


async def test_inactive_or_roleless_admin_and_stranger_are_not_admins(service, db_session) -> None:
    inactive = await make_admin_user(db_session, await make_role(db_session), is_active=False)
    roleless = await make_admin_user(db_session)

    assert not await service.is_admin(inactive.tg_id)
    assert not await service.is_admin(roleless.tg_id)
    assert not await service.is_admin(1)
