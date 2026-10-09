from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository
from app.models import AppSettings
from app.models.app_settings import APP_SETTINGS_ID


class AppSettingsRepository(BaseRepository[AppSettings]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AppSettings)

    async def get(self) -> AppSettings | None:
        return await self.get_by_id(APP_SETTINGS_ID)
