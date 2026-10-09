from datetime import UTC, datetime

from app.repositories import BlockRepository
from tests.factories import make_block, make_club

NOW = datetime(2026, 10, 1, tzinfo=UTC)


async def test_current_block_is_the_one_running_now(db_session) -> None:
    club = await make_club(db_session)
    await make_block(db_session, club, starts_at=datetime(2026, 7, 1, tzinfo=UTC))
    running = await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    await make_block(db_session, club, starts_at=datetime(2026, 11, 1, tzinfo=UTC))

    current = await BlockRepository(db_session).get_current_for_club(club_id=club.id, now=NOW)

    assert current is running


async def test_overlapping_blocks_resolve_to_the_latest_started(db_session) -> None:
    club = await make_club(db_session)
    await make_block(db_session, club, starts_at=datetime(2026, 8, 15, tzinfo=UTC))
    latest = await make_block(db_session, club, starts_at=datetime(2026, 9, 15, tzinfo=UTC))

    current = await BlockRepository(db_session).get_current_for_club(club_id=club.id, now=NOW)

    assert current is latest


async def test_no_current_block_between_blocks_or_in_another_club(db_session) -> None:
    club = await make_club(db_session)
    other = await make_club(db_session)
    await make_block(db_session, club, starts_at=datetime(2026, 11, 1, tzinfo=UTC))
    await make_block(db_session, other, starts_at=datetime(2026, 9, 1, tzinfo=UTC))

    current = await BlockRepository(db_session).get_current_for_club(club_id=club.id, now=NOW)

    assert current is None
