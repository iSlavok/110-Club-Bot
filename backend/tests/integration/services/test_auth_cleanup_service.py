from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import AdminSession, LoginCode, VkAuthRequest
from app.services import AuthCleanupService
from tests.factories import (
    make_admin_session,
    make_admin_user,
    make_login_code,
    make_role,
    make_user,
    make_vk_auth_request,
)
from tests.providers import DEFAULT_NOW

PAST = DEFAULT_NOW - timedelta(minutes=1)
FUTURE = DEFAULT_NOW + timedelta(minutes=5)


@pytest.fixture
async def service(request_container) -> AuthCleanupService:
    return await request_container.get(AuthCleanupService)


async def test_purge_removes_only_spent_codes_and_expired_sessions(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    await make_admin_session(db_session, admin, expires_at=PAST)
    active_session = await make_admin_session(db_session, admin, expires_at=FUTURE)
    await make_login_code(db_session, admin, expires_at=PAST)
    await make_login_code(db_session, admin, expires_at=FUTURE, used_at=PAST)
    active_code = await make_login_code(db_session, admin, expires_at=FUTURE)

    await service.purge_expired()

    db_session.expunge_all()
    assert list(await db_session.scalars(select(AdminSession.id))) == [active_session.id]
    assert list(await db_session.scalars(select(LoginCode.id))) == [active_code.id]


async def test_purge_removes_spent_vk_auth_requests(service, db_session) -> None:
    user = await make_user(db_session)
    await make_vk_auth_request(db_session, user, expires_at=PAST)
    await make_vk_auth_request(db_session, user, expires_at=FUTURE, used_at=PAST)
    active = await make_vk_auth_request(db_session, user, expires_at=FUTURE)

    await service.purge_expired()

    db_session.expunge_all()
    assert list(await db_session.scalars(select(VkAuthRequest.id))) == [active.id]
