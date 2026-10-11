from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer, make_async_container
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.ioc import DatabaseProvider
from app.models import Club
from tests.factories import make_club
from tests.providers import ConnectionSessionmakerProvider


@pytest.fixture
async def app_container(connection: AsyncConnection) -> AsyncIterator[AsyncContainer]:
    container = make_async_container(DatabaseProvider(), ConnectionSessionmakerProvider(connection))
    yield container
    await container.close()


async def _clubs_titled(connection: AsyncConnection, title: str) -> int:
    statement = select(func.count()).select_from(Club).where(Club.title == title)
    return await connection.scalar(statement) or 0


async def test_successful_scope_commits(app_container, connection) -> None:
    async with app_container() as scope:
        await make_club(await scope.get(AsyncSession), title="Сохранится")

    assert await _clubs_titled(connection, "Сохранится") == 1


async def _create_club_and_fail(app_container: AsyncContainer) -> None:
    async with app_container() as scope:
        await make_club(await scope.get(AsyncSession), title="Откатится")
        raise RuntimeError


async def test_failed_scope_rolls_back(app_container, connection) -> None:
    with pytest.raises(RuntimeError):
        await _create_club_and_fail(app_container)

    assert await _clubs_titled(connection, "Откатится") == 0
