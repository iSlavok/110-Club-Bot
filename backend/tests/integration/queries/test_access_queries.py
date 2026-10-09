from datetime import UTC, datetime

import pytest

from app.queries import AccessQueries
from app.queries.rows import CurrentBlockRow
from tests.factories import make_block, make_club, make_membership
from tests.providers import DEFAULT_NOW

VK_ID = 4242


@pytest.fixture
async def queries(request_container) -> AccessQueries:
    return await request_container.get(AccessQueries)


async def test_lists_only_current_blocks_of_active_clubs(queries, db_session) -> None:
    club = await make_club(db_session, title="Химия")
    current = await make_block(db_session, club, title="Блок 5")
    past = await make_block(db_session, club, title="Блок 4", starts_at=datetime(2026, 6, 1, tzinfo=UTC))
    upcoming = await make_block(db_session, club, title="Блок 6", starts_at=datetime(2026, 10, 2, tzinfo=UTC))
    inactive_club = await make_club(db_session, title="Архив", is_active=False)
    inactive_block = await make_block(db_session, inactive_club)
    for block in (current, past, upcoming, inactive_block):
        await make_membership(db_session, block, vk_id=VK_ID)
    await make_membership(db_session, current)

    rows = await queries.current_blocks_for_vk(vk_id=VK_ID, now=DEFAULT_NOW)

    assert rows == [CurrentBlockRow(club_title="Химия", block_title="Блок 5")]


async def test_block_is_over_at_its_end(queries, db_session) -> None:
    block = await make_block(db_session, await make_club(db_session))
    await make_membership(db_session, block, vk_id=VK_ID)

    assert await queries.current_blocks_for_vk(vk_id=VK_ID, now=block.ends_at) == []
