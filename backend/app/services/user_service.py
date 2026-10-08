from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import UserRepository
from app.schemas import TelegramProfile, UserDTO


class UserService:
    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        self._session = session
        self._user_repository = user_repository

    async def register(self, profile: TelegramProfile) -> UserDTO:
        user = await self._user_repository.upsert_by_tg_id(
            tg_id=profile.tg_id,
            tg_username=profile.tg_username,
            full_name=profile.full_name,
        )
        await self._session.commit()
        return UserDTO.from_orm_obj(user)
