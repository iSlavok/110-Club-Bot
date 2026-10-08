from app.exceptions import ClubNotFoundError, ClubTitleTakenError, EmptyUpdateError
from app.models import Club
from app.repositories import ClubRepository
from app.schemas import ClubCreate, ClubDTO, ClubUpdate, PageParams, Paginated


class ClubService:
    def __init__(self, club_repository: ClubRepository) -> None:
        self._club_repository = club_repository

    async def list_page(self, page: PageParams) -> Paginated[ClubDTO]:
        clubs = await self._club_repository.list_page(limit=page.per_page, offset=page.offset)
        return Paginated(items=[ClubDTO.from_orm_obj(club) for club in clubs.items], total=clubs.total)

    async def get(self, club_id: int) -> ClubDTO:
        club = await self._get(club_id)
        return ClubDTO.from_orm_obj(club)

    async def create(self, data: ClubCreate) -> ClubDTO:
        await self._ensure_title_free(data.title)
        club = Club(
            title=data.title,
            chat_id=data.chat_id,
            reminders_topic_id=data.reminders_topic_id,
            spreadsheet_id=data.spreadsheet_id,
            sheet_name=data.sheet_name,
        )
        self._club_repository.add(club)
        await self._club_repository.flush()
        return ClubDTO.from_orm_obj(club)

    async def update(self, club_id: int, patch: ClubUpdate) -> ClubDTO:
        if patch.is_empty():
            raise EmptyUpdateError
        club = await self._get(club_id)
        if patch.title.is_set and patch.title.value != club.title:
            await self._ensure_title_free(patch.title.apply(club.title))
        club.title = patch.title.apply(club.title)
        club.chat_id = patch.chat_id.apply(club.chat_id)
        club.reminders_topic_id = patch.reminders_topic_id.apply(club.reminders_topic_id)
        club.spreadsheet_id = patch.spreadsheet_id.apply(club.spreadsheet_id)
        club.sheet_name = patch.sheet_name.apply(club.sheet_name)
        club.is_active = patch.is_active.apply(club.is_active)
        await self._club_repository.flush()
        return ClubDTO.from_orm_obj(club)

    async def _get(self, club_id: int) -> Club:
        club = await self._club_repository.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        return club

    async def _ensure_title_free(self, title: str) -> None:
        if await self._club_repository.get_by_title(title) is not None:
            raise ClubTitleTakenError(title)
