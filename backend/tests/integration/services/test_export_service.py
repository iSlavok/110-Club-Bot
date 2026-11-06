from datetime import UTC, datetime

import pytest

from app.enums import BlockMemberState, ChatAccessStatus
from app.exceptions import BlockNotFoundError
from app.services import ExportService
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user
from tests.xlsx import read_xlsx


@pytest.fixture
async def service(request_container) -> ExportService:
    return await request_container.get(ExportService)


async def test_block_members_export_follows_the_filter(service, db_session) -> None:
    club = await make_club(db_session, chat_id=-100500)
    block = await make_block(db_session, club)
    for vk_id in (501, 502, 503):
        await make_membership(db_session, block, vk_id=vk_id)
    joined = await make_user(db_session, vk_id=501, full_name="Борис", tg_username="boris")
    await make_user(db_session, vk_id=502, full_name="Анна", tg_username=None)
    await make_chat_access(
        db_session,
        club,
        joined,
        status=ChatAccessStatus.JOINED,
        joined_at=datetime(2026, 9, 2, 7, 0, tzinfo=UTC),
    )

    everyone = await service.block_members(block.id, state=None, query=None)
    not_in_chat = await service.block_members(block.id, state=BlockMemberState.NOT_IN_CHAT, query=None)

    assert everyone.filename == f"block-{block.id}-all.xlsx"
    assert read_xlsx(everyone.content)[1:] == [
        ["https://vk.com/id502", 502, "Анна", None, "подключил", None, None],
        ["https://vk.com/id501", 501, "Борис", "@boris", "подключил", "в чате", "02.09.2026 10:00"],
        ["https://vk.com/id503", 503, None, None, "не подключил", None, None],
    ]
    assert not_in_chat.filename == f"block-{block.id}-not-in-chat.xlsx"
    assert [row[1] for row in read_xlsx(not_in_chat.content)[1:]] == [502, 503]


async def test_block_members_export_of_unknown_block(service) -> None:
    with pytest.raises(BlockNotFoundError):
        await service.block_members(999_999, state=None, query=None)


async def test_users_export_follows_the_search(service, db_session) -> None:
    await make_user(db_session, full_name="Анна Белова", vk_id=601)
    await make_user(db_session, full_name="Борис")

    file = await service.users("анна")

    rows = read_xlsx(file.content)
    assert rows[0][0] == "Имя в Telegram"
    assert [(row[0], row[3]) for row in rows[1:]] == [("Анна Белова", "https://vk.com/id601")]
