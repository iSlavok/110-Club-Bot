from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SystemQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ping_database(self) -> None:
        await self._session.execute(text("SELECT 1"))
