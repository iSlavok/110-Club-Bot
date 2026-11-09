from app.repositories import UserRepository
from app.schemas import PageParams, Paginated, TelegramProfile, UserDTO
from app.utils import Clock


class UserService:
    def __init__(self, user_repository: UserRepository, clock: Clock) -> None:
        self._user_repository = user_repository
        self._clock = clock

    async def register(self, profile: TelegramProfile) -> UserDTO:
        user = await self._user_repository.upsert_by_tg_id(
            tg_id=profile.tg_id,
            tg_username=profile.tg_username,
            full_name=profile.full_name,
        )
        # A user writing to the bot has not blocked it.
        if user.bot_blocked_at is not None:
            user.bot_blocked_at = None
            await self._user_repository.flush()
        return UserDTO.from_orm_obj(user)

    # Telegram reports blocking and unblocking the bot in the private chat; a user who never started it is unknown.
    async def set_bot_blocked(self, tg_id: int, *, blocked: bool) -> None:
        user = await self._user_repository.get_by_tg_id(tg_id)
        if user is None or (user.bot_blocked_at is not None) == blocked:
            return
        user.bot_blocked_at = self._clock.now() if blocked else None
        await self._user_repository.flush()

    async def find_by_tg_id(self, tg_id: int) -> UserDTO | None:
        user = await self._user_repository.get_by_tg_id(tg_id)
        return None if user is None else UserDTO.from_orm_obj(user)

    async def search_page(self, query: str | None, page: PageParams) -> Paginated[UserDTO]:
        users = await self._user_repository.search_page(query=query, limit=page.per_page, offset=page.offset)
        return Paginated(items=[UserDTO.from_orm_obj(user) for user in users.items], total=users.total)
