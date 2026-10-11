from app.enums import ChatAccessStatus
from app.repositories import ChatAccessRepository
from tests.factories import make_chat_access, make_club, make_user

CHAT_ID = -100500


async def test_counts_by_status_in_the_current_chat_only(db_session) -> None:
    club = await make_club(db_session, chat_id=CHAT_ID)
    for status in (ChatAccessStatus.JOINED, ChatAccessStatus.JOINED, ChatAccessStatus.INVITED):
        await make_chat_access(db_session, club, await make_user(db_session), status=status)
    await make_chat_access(db_session, club, await make_user(db_session), chat_id=CHAT_ID - 1)

    counts = await ChatAccessRepository(db_session).count_by_status(club_id=club.id, chat_id=CHAT_ID)

    assert counts == {ChatAccessStatus.JOINED: 2, ChatAccessStatus.INVITED: 1}
