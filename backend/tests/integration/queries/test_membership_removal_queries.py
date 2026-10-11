import pytest

from app.enums import RemovalRequestStatus
from app.queries import MembershipRemovalQueries
from tests.factories import make_block, make_club, make_removal_request


@pytest.fixture
async def queries(request_container) -> MembershipRemovalQueries:
    return await request_container.get(MembershipRemovalQueries)


async def test_counts_pending_requests_of_the_club_blocks(queries, db_session) -> None:
    club = await make_club(db_session)
    first_block = await make_block(db_session, club)
    second_block = await make_block(db_session, club)
    await make_removal_request(db_session, first_block, 101)
    await make_removal_request(db_session, second_block, 102)
    await make_removal_request(db_session, first_block, 103, status=RemovalRequestStatus.CONFIRMED)
    await make_removal_request(db_session, first_block, 104, status=RemovalRequestStatus.REJECTED)
    await make_removal_request(db_session, first_block, 105, status=RemovalRequestStatus.CANCELLED)
    other_block = await make_block(db_session, await make_club(db_session))
    await make_removal_request(db_session, other_block, 106)

    count = await queries.count_pending_for_club(club.id)

    assert count == 2


async def test_club_without_requests(queries, db_session) -> None:
    club = await make_club(db_session)

    count = await queries.count_pending_for_club(club.id)

    assert count == 0
