from datetime import UTC, datetime

import pytest

from app.exceptions import ClubNotFoundError
from app.services import ClubStatsService
from tests.factories import make_block, make_club, make_membership, make_sheet_sync, make_user


@pytest.fixture
async def service(request_container) -> ClubStatsService:
    return await request_container.get(ClubStatsService)


async def test_counts_members_of_the_current_block(service, db_session) -> None:
    club = await make_club(db_session)
    block = await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    membership = await make_membership(db_session, block)
    await make_membership(db_session, block)
    await make_user(db_session, vk_id=membership.vk_id)

    stats = await service.get(club.id)

    assert stats.current_block is not None
    assert stats.current_block.block.id == block.id
    assert stats.current_block.members == 2
    assert stats.current_block.members_with_tg == 1


async def test_no_current_block(service, db_session, clock) -> None:
    club = await make_club(db_session)
    await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    clock.set(datetime(2027, 1, 1, tzinfo=UTC))

    stats = await service.get(club.id)

    assert stats.current_block is None


async def test_latest_sync(service, db_session) -> None:
    club = await make_club(db_session)
    await make_sheet_sync(db_session, club, started_at=datetime(2026, 10, 1, 8, 0, tzinfo=UTC))
    latest = await make_sheet_sync(db_session, club, started_at=datetime(2026, 10, 1, 8, 10, tzinfo=UTC))
    await make_sheet_sync(db_session, await make_club(db_session), started_at=datetime(2026, 10, 1, 8, 20, tzinfo=UTC))

    stats = await service.get(club.id)

    assert stats.last_sync is not None
    assert stats.last_sync.id == latest.id


async def test_never_synced(service, db_session) -> None:
    club = await make_club(db_session)

    stats = await service.get(club.id)

    assert stats.last_sync is None


async def test_unknown_club(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.get(10**9)
