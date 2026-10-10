from app.repositories import MembershipRepository
from tests.factories import make_block, make_club, make_membership

VK_ID = 4242


async def test_member_only_of_the_block_they_are_listed_in(db_session) -> None:
    club = await make_club(db_session)
    block = await make_block(db_session, club)
    other = await make_block(db_session, club)
    await make_membership(db_session, block, vk_id=VK_ID)
    repository = MembershipRepository(db_session)

    assert await repository.is_member(block_id=block.id, vk_id=VK_ID)
    assert not await repository.is_member(block_id=other.id, vk_id=VK_ID)
