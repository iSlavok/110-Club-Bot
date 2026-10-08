from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer, make_async_container
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import Session
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api import create_app
from api.core.auth import SESSION_COOKIE
from app.enums import Permission
from app.ioc import DatabaseProvider, QueriesProvider, RepositoriesProvider, ServicesProvider
from app.models import AdminUser
from app.services import AdminAccessResolver, AdminSessionService
from tests import providers
from tests.factories import make_admin_user, make_role


@pytest.fixture
async def uow_container(connection: AsyncConnection) -> AsyncIterator[AsyncContainer]:
    container = make_async_container(
        DatabaseProvider(),
        providers.ConnectionSessionmakerProvider(connection),
        providers.TestInfraProvider(),
        RepositoriesProvider(),
        QueriesProvider(),
        ServicesProvider(),
    )
    yield container
    await container.close()


async def _logged_in_client(container: AsyncContainer, app: ASGIApp, admin: AdminUser) -> AsyncClient:
    async with container() as scope:
        principal = (await scope.get(AdminAccessResolver)).resolve(admin)
        assert principal is not None
        grant = await (await scope.get(AdminSessionService)).start(principal)
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    client.cookies.set(SESSION_COOKIE, grant.token)
    return client


async def test_domain_error_rolls_back_partial_changes(uow_container, connection) -> None:
    async with uow_container() as scope:
        session = await scope.get(AsyncSession)
        editor = await make_admin_user(session, await make_role(session, Permission.ADMINS_EDIT, Permission.USERS_VIEW))
        target = await make_admin_user(session, await make_role(session, Permission.USERS_VIEW), name="Старое имя")
        stronger_role = await make_role(session, Permission.ROLES_EDIT)

    async with await _logged_in_client(uow_container, create_app(uow_container), editor) as client:
        response = await client.patch(
            f"/api/v1/admins/{target.id}",
            json={"name": "Новое имя", "role_id": stronger_role.id},
        )

    assert response.status_code == 403
    assert await connection.scalar(select(AdminUser.name).where(AdminUser.id == target.id)) == "Старое имя"


async def test_commit_happens_before_the_response_is_sent(uow_container) -> None:
    async with uow_container() as scope:
        session = await scope.get(AsyncSession)
        editor = await make_admin_user(session, await make_role(session, Permission.ADMINS_EDIT, Permission.USERS_VIEW))
        target = await make_admin_user(session, await make_role(session, Permission.USERS_VIEW))
    events: list[str] = []

    def record_send(app: ASGIApp) -> ASGIApp:
        async def wrapped(scope: Scope, receive: Receive, send: Send) -> None:
            async def spy(message: Message) -> None:
                events.append(message["type"])
                await send(message)

            await app(scope, receive, spy)

        return wrapped

    def record_commit(_session: Session) -> None:
        events.append("commit")

    app = record_send(create_app(uow_container))
    event.listen(Session, "after_commit", record_commit)
    try:
        async with await _logged_in_client(uow_container, app, editor) as client:
            events.clear()
            await client.patch(f"/api/v1/admins/{target.id}", json={"name": "Новое имя"})
    finally:
        event.remove(Session, "after_commit", record_commit)

    assert events[:2] == ["commit", "http.response.start"]
