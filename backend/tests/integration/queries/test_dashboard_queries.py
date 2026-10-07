from datetime import UTC, datetime

from app.queries import DashboardQueries
from tests.factories import make_block, make_club, make_user

NOW = datetime(2026, 10, 1, tzinfo=UTC)


async def test_counts(db_session) -> None:
    club = await make_club(db_session)
    archived = await make_club(db_session, is_active=False)
    await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    await make_block(db_session, club, starts_at=datetime(2026, 12, 1, tzinfo=UTC))
    await make_block(db_session, archived, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    await make_user(db_session, vk_id=1)
    await make_user(db_session)

    counts = await DashboardQueries(db_session).counts(NOW)

    assert counts.active_clubs == 1
    assert counts.current_blocks == 1
    assert counts.users == 2
    assert counts.users_with_vk == 1
