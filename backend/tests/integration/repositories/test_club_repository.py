from app.repositories import ClubRepository
from tests.factories import make_club

CHAT_ID = -100500


async def test_finds_the_active_club_of_a_chat(db_session) -> None:
    await make_club(db_session, chat_id=CHAT_ID, is_active=False)
    club = await make_club(db_session, chat_id=CHAT_ID)

    assert await ClubRepository(db_session).get_active_by_chat_id(CHAT_ID) is club


async def test_lists_active_clubs_with_a_chat(db_session) -> None:
    club = await make_club(db_session, chat_id=CHAT_ID)
    await make_club(db_session)
    await make_club(db_session, chat_id=CHAT_ID - 1, is_active=False)

    assert await ClubRepository(db_session).list_with_chat() == [club]
