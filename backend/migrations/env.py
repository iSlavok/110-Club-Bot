import asyncio

from alembic import context
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app import models  # noqa: F401 - registers every model on Base.metadata
from app.config import DatabaseSettings
from app.database import Base


class _MigrationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1, extra="ignore")

    db: DatabaseSettings


def _run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_server_default=True)
    with context.begin_transaction():
        context.run_migrations()


async def _run_with_own_engine() -> None:
    settings = _MigrationSettings()  # pyright: ignore[reportCallIssue] - DB_* come from the environment
    engine = create_async_engine(settings.db.url)
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
    await engine.dispose()


# Tests hand over their own connection to migrate the test database without reading the environment.
connection: Connection | None = context.config.attributes.get("connection")
if connection is not None:
    _run_migrations(connection)
else:
    asyncio.run(_run_with_own_engine())
