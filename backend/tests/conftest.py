import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from dishka import AsyncContainer, make_async_container
from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.ioc import QueriesProvider, RepositoriesProvider, ServicesProvider
from app.utils import Clock
from tests.fakes import FrozenClock
from tests.providers import TestDatabaseProvider, TestInfraProvider

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5433/test")


def _migrate(connection: Connection) -> None:
    connection.execute(text("DROP SCHEMA public CASCADE"))
    connection.execute(text("CREATE SCHEMA public"))
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(_migrate)
    yield engine
    await engine.dispose()


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        yield connection
        await transaction.rollback()


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        # Services call commit(); a savepoint turns it into a release so the outer rollback still isolates tests.
        session = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def container(db_session: AsyncSession) -> AsyncIterator[AsyncContainer]:
    container = make_async_container(
        TestDatabaseProvider(db_session),
        TestInfraProvider(),
        RepositoriesProvider(),
        QueriesProvider(),
        ServicesProvider(),
    )
    yield container
    await container.close()


@pytest.fixture
async def request_container(container: AsyncContainer) -> AsyncIterator[AsyncContainer]:
    async with container() as request_container:
        yield request_container


@pytest.fixture
async def clock(container: AsyncContainer) -> FrozenClock:
    return cast("FrozenClock", await container.get(Clock))
