from app.queries import ClubStatsQueries
from tests.factories import make_block, make_club, make_membership, make_user


async def test_block_member_counts(db_session) -> None:
    club = await make_club(db_session)
    block = await make_block(db_session, club)
    other_block = await make_block(db_session, club)
    linked = await make_membership(db_session, block)
    await make_membership(db_session, block)
    await make_membership(db_session, other_block)
    await make_user(db_session, vk_id=linked.vk_id)
    await make_user(db_session, vk_id=1)

    counts = await ClubStatsQueries(db_session).block_member_counts(block.id)

    assert counts.members == 2
    assert counts.members_with_tg == 1
