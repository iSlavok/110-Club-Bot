from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base


class BaseRepository[ModelType: Base]:
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, id_: int) -> ModelType | None:
        return await self._session.get(self._model, id_)

    def add(self, obj: ModelType) -> None:
        self._session.add(obj)

    async def delete(self, obj: ModelType) -> None:
        await self._session.delete(obj)

    async def flush(self) -> None:
        await self._session.flush()
