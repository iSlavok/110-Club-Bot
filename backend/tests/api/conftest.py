from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer
from httpx import ASGITransport, AsyncClient

from api import create_app


@pytest.fixture
async def api_client(container: AsyncContainer) -> AsyncIterator[AsyncClient]:
    app = create_app(container)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
