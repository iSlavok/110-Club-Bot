import pytest

from app.enums import ChatAccessStatus
from app.queries import ChatAccessQueries
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user

CHAT_ID = -100500


@pytest.fixture
async def queries(request_container) -> ChatAccessQueries:
    return await request_container.get(ChatAccessQueries)


async def test_invites_linked_members_the_bot_has_not_let_in(queries, db_session) -> None:
    club = await make_club(db_session, chat_id=CHAT_ID)
    block = await make_block(db_session, club)
    new = await make_user(db_session, vk_id=1)
    kicked = await make_user(db_session, vk_id=2)
    moved_chat = await make_user(db_session, vk_id=3)
    joined = await make_user(db_session, vk_id=4)
    invited = await make_user(db_session, vk_id=5)
    for vk_id in (1, 2, 3, 4, 5, 6):
        await make_membership(db_session, block, vk_id=vk_id)
    await make_chat_access(db_session, club, kicked, status=ChatAccessStatus.KICKED)
    await make_chat_access(db_session, club, moved_chat, chat_id=CHAT_ID - 1)
    await make_chat_access(db_session, club, joined)
    await make_chat_access(db_session, club, invited, status=ChatAccessStatus.INVITED)
    await make_user(db_session, vk_id=7)

    user_ids = await queries.list_users_to_invite(club_id=club.id, chat_id=CHAT_ID, block_id=block.id)

    assert user_ids == [new.id, kicked.id, moved_chat.id]


async def test_joined_without_access_are_those_out_of_the_block(queries, db_session) -> None:
    club = await make_club(db_session, chat_id=CHAT_ID)
    block = await make_block(db_session, club)
    await make_membership(db_session, block, vk_id=1)
    stays = await make_chat_access(db_session, club, await make_user(db_session, vk_id=1))
    leaves = await make_chat_access(db_session, club, await make_user(db_session, vk_id=2))
    await make_chat_access(db_session, club, await make_user(db_session, vk_id=3), status=ChatAccessStatus.INVITED)
    await make_chat_access(db_session, club, await make_user(db_session, vk_id=4), chat_id=CHAT_ID - 1)

    with_block = await queries.list_joined_without_access(club_id=club.id, chat_id=CHAT_ID, block_id=block.id)
    without_block = await queries.list_joined_without_access(club_id=club.id, chat_id=CHAT_ID, block_id=None)

    assert with_block == [leaves.id]
    assert without_block == [stays.id, leaves.id]
