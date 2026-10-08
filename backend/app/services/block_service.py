from app.exceptions import (
    BlockColumnTakenError,
    BlockHasMembersError,
    BlockNotFoundError,
    ClubNotFoundError,
    EmptyUpdateError,
    InvalidBlockPeriodError,
)
from app.models import Block
from app.repositories import BlockRepository, ClubRepository, MembershipRepository
from app.schemas import BlockCreate, BlockDTO, BlockUpdate, PageParams, Paginated


class BlockService:
    def __init__(
        self,
        block_repository: BlockRepository,
        club_repository: ClubRepository,
        membership_repository: MembershipRepository,
    ) -> None:
        self._block_repository = block_repository
        self._club_repository = club_repository
        self._membership_repository = membership_repository

    async def list_page(self, club_id: int, page: PageParams) -> Paginated[BlockDTO]:
        await self._ensure_club_exists(club_id)
        blocks = await self._block_repository.list_page_for_club(
            club_id=club_id,
            limit=page.per_page,
            offset=page.offset,
        )
        return Paginated(items=[BlockDTO.from_orm_obj(block) for block in blocks.items], total=blocks.total)

    async def create(self, club_id: int, data: BlockCreate) -> BlockDTO:
        await self._ensure_club_exists(club_id)
        await self._ensure_column_free(club_id, data.sheet_column_title)
        block = Block(
            club_id=club_id,
            title=data.title,
            sheet_column_title=data.sheet_column_title,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
        self._block_repository.add(block)
        await self._block_repository.flush()
        return BlockDTO.from_orm_obj(block)

    async def update(self, block_id: int, patch: BlockUpdate) -> BlockDTO:
        if patch.is_empty():
            raise EmptyUpdateError
        block = await self._get(block_id)
        if patch.sheet_column_title.is_set and patch.sheet_column_title.value != block.sheet_column_title:
            await self._ensure_column_free(block.club_id, patch.sheet_column_title.apply(block.sheet_column_title))
        starts_at = patch.starts_at.apply(block.starts_at)
        ends_at = patch.ends_at.apply(block.ends_at)
        if ends_at <= starts_at:
            raise InvalidBlockPeriodError
        block.title = patch.title.apply(block.title)
        block.sheet_column_title = patch.sheet_column_title.apply(block.sheet_column_title)
        block.starts_at = starts_at
        block.ends_at = ends_at
        await self._block_repository.flush()
        return BlockDTO.from_orm_obj(block)

    async def delete(self, block_id: int) -> None:
        block = await self._get(block_id)
        if await self._membership_repository.exists_for_block(block.id):
            raise BlockHasMembersError
        await self._block_repository.delete(block)
        await self._block_repository.flush()

    async def _get(self, block_id: int) -> Block:
        block = await self._block_repository.get_by_id(block_id)
        if block is None:
            raise BlockNotFoundError(block_id)
        return block

    async def _ensure_club_exists(self, club_id: int) -> None:
        if await self._club_repository.get_by_id(club_id) is None:
            raise ClubNotFoundError(club_id)

    async def _ensure_column_free(self, club_id: int, sheet_column_title: str) -> None:
        if await self._block_repository.get_by_column(club_id=club_id, sheet_column_title=sheet_column_title):
            raise BlockColumnTakenError(sheet_column_title)
