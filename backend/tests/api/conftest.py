from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from dishka import AsyncContainer
from httpx import ASGITransport, AsyncClient

from api import create_app
from api.core.auth import SESSION_COOKIE
from app.models import AdminUser
from app.services import AdminAccessResolver, AdminSessionService

type LoginAs = Callable[[AdminUser], Awaitable[None]]


@pytest.fixture
async def api_client(container: AsyncContainer) -> AsyncIterator[AsyncClient]:
    app = create_app(container)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def login_as(api_client: AsyncClient, request_container: AsyncContainer) -> LoginAs:
    async def login(admin: AdminUser) -> None:
        resolver = await request_container.get(AdminAccessResolver)
        principal = resolver.resolve(admin)
        assert principal is not None, "admin has no access to log in"
        grant = await (await request_container.get(AdminSessionService)).start(principal)
        api_client.cookies.set(SESSION_COOKIE, grant.token)

    return login
