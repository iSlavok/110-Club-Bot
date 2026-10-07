from datetime import UTC, datetime

import pytest

from app.exceptions import (
    BlockColumnTakenError,
    BlockHasMembersError,
    BlockNotFoundError,
    ClubNotFoundError,
    InvalidBlockPeriodError,
)
from app.schemas import BlockCreate, BlockUpdate, PageParams
from app.services import BlockService
from tests.factories import make_block, make_club, make_membership

SEPT = datetime(2026, 9, 1, tzinfo=UTC)
NOV = datetime(2026, 11, 1, tzinfo=UTC)


@pytest.fixture
async def service(request_container) -> BlockService:
    return await request_container.get(BlockService)


async def test_create_block(service, db_session) -> None:
    club = await make_club(db_session)

    block = await service.create(
        club.id,
        BlockCreate(title="Блок 5", sheet_column_title="Блок 5", starts_at=SEPT, ends_at=NOV),
    )

    assert block.club_id == club.id
    assert block.starts_at == SEPT


async def test_create_in_unknown_club(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.create(999_999, BlockCreate(title="X", sheet_column_title="X", starts_at=SEPT, ends_at=NOV))


async def test_column_is_unique_within_club(service, db_session) -> None:
    club = await make_club(db_session)
    await make_block(db_session, club, sheet_column_title="Блок 5")
    other_club = await make_club(db_session)

    with pytest.raises(BlockColumnTakenError):
        await service.create(club.id, BlockCreate(title="X", sheet_column_title="Блок 5", starts_at=SEPT, ends_at=NOV))
    await service.create(
        other_club.id, BlockCreate(title="X", sheet_column_title="Блок 5", starts_at=SEPT, ends_at=NOV)
    )


def test_create_requires_end_after_start() -> None:
    with pytest.raises(ValueError, match="ends_at"):
        BlockCreate(title="X", sheet_column_title="X", starts_at=NOV, ends_at=SEPT)


async def test_update_checks_period_against_stored_dates(service, db_session) -> None:
    block = await make_block(db_session, await make_club(db_session), starts_at=SEPT)

    with pytest.raises(InvalidBlockPeriodError):
        await service.update(block.id, BlockUpdate.model_validate({"ends_at": SEPT}))


async def test_block_with_members_is_not_deleted(service, db_session) -> None:
    block = await make_block(db_session, await make_club(db_session))
    await make_membership(db_session, block)

    with pytest.raises(BlockHasMembersError):
        await service.delete(block.id)


async def test_delete_block(service, db_session) -> None:
    block = await make_block(db_session, await make_club(db_session))

    await service.delete(block.id)

    with pytest.raises(BlockNotFoundError):
        await service.update(block.id, BlockUpdate.model_validate({"title": "X"}))


async def test_list_newest_first(service, db_session) -> None:
    club = await make_club(db_session)
    await make_block(db_session, club, title="Старый", starts_at=SEPT)
    await make_block(db_session, club, title="Новый", starts_at=NOV)

    page = await service.list_page(club.id, PageParams())

    assert [block.title for block in page.items] == ["Новый", "Старый"]
