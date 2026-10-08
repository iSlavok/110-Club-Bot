from collections.abc import AsyncGenerator, AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import DatabaseSettings
from app.database import create_engine, create_sessionmaker


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self, settings: DatabaseSettings) -> AsyncIterator[AsyncEngine]:
        engine = create_engine(settings)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def sessionmaker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_sessionmaker(engine)

    # One request scope = one unit of work: an HTTP request, a bot update or a job run.
    # dishka sends the scope's exception back into the generator; closing the session rolls back.
    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, BaseException | None]:
        async with sessionmaker() as session:
            exception = yield session
            if exception is None:
                await session.commit()
