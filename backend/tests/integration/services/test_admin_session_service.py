from datetime import timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.enums import Permission
from app.exceptions import NotAuthenticatedError
from app.services import AdminAccessResolver, AdminSessionService
from tests.factories import make_admin_user, make_role
from tests.providers import DEFAULT_NOW, OWNER_TG_ID


@pytest.fixture
async def service(request_container) -> AdminSessionService:
    return await request_container.get(AdminSessionService)


@pytest.fixture
async def resolver(request_container) -> AdminAccessResolver:
    return await request_container.get(AdminAccessResolver)


async def _start(service, resolver, admin) -> str:
    principal = resolver.resolve(admin)
    assert principal is not None
    return (await service.start(principal)).token


async def test_session_authenticates_with_current_permissions(service, resolver, db_session) -> None:
    role = await make_role(db_session, Permission.USERS_VIEW)
    admin = await make_admin_user(db_session, role)
    token = await _start(service, resolver, admin)
    role.permissions = [Permission.CLUBS_VIEW, "removed.permission"]
    await db_session.flush()

    principal = await service.authenticate(token)

    assert principal.id == admin.id
    assert principal.permissions == {Permission.CLUBS_VIEW}


async def test_owner_has_every_permission(service, resolver, db_session) -> None:
    owner = await make_admin_user(db_session, tg_id=OWNER_TG_ID)

    principal = await service.authenticate(await _start(service, resolver, owner))

    assert principal.is_owner
    assert principal.permissions == set(Permission)


@pytest.mark.parametrize("token", [None, "", "unknown"])
async def test_missing_or_unknown_token_is_rejected(service, token) -> None:
    with pytest.raises(NotAuthenticatedError):
        await service.authenticate(token)


async def test_expired_session_is_rejected(service, resolver, db_session, clock) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    token = await _start(service, resolver, admin)
    clock.set(DEFAULT_NOW + timedelta(days=31))

    with pytest.raises(NotAuthenticatedError):
        await service.authenticate(token)


async def test_deactivated_admin_loses_session(service, resolver, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    token = await _start(service, resolver, admin)
    admin.is_active = False
    await db_session.flush()

    with pytest.raises(NotAuthenticatedError):
        await service.authenticate(token)


async def test_ended_session_is_rejected(service, resolver, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    token = await _start(service, resolver, admin)

    await service.end(token)

    with pytest.raises(NotAuthenticatedError):
        await service.authenticate(token)


async def test_authentication_takes_a_single_query(service, resolver, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session, Permission.USERS_VIEW))
    token = await _start(service, resolver, admin)
    await db_session.flush()
    db_session.expunge_all()
    statements: list[str] = []

    def record(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", record)
    try:
        await service.authenticate(token)
    finally:
        event.remove(Engine, "before_cursor_execute", record)

    assert len(statements) == 1
