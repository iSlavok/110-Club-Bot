from datetime import UTC, datetime

import pytest

from app.clients import SheetsClientError
from app.enums import ChatAccessStatus
from app.exceptions import StatusSheetWriteError
from app.services import StatusSheetService
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user

NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
TITLE_TAIL = "обновлено 01.10.2026 12:00"


@pytest.fixture
async def service(request_container, clock) -> StatusSheetService:
    clock.set(NOW)
    return await request_container.get(StatusSheetService)


async def test_lists_the_access_block_by_funnel_step(service, db_session, sheets_client) -> None:
    club = await make_club(db_session, chat_id=-100500, spreadsheet_id="s1", status_sheet_name="Статус")
    block = await make_block(
        db_session,
        club,
        title="5",
        starts_at=datetime(2026, 9, 1, tzinfo=UTC),
        ends_at=datetime(2026, 11, 1, tzinfo=UTC),
    )
    for vk_id in (501, 502, 503, 504):
        await make_membership(db_session, block, vk_id=vk_id)
    joined = await make_user(db_session, vk_id=501)
    invited = await make_user(db_session, vk_id=502)
    await make_chat_access(db_session, club, joined, status=ChatAccessStatus.JOINED)
    await make_chat_access(db_session, club, invited, status=ChatAccessStatus.INVITED)

    await service.publish(club.id)

    assert sheets_client.written["s1", "Статус"] == [
        [f"Блок «5» · {TITLE_TAIL}"],
        [],
        ["Не подключили бота (2)", "Зашли в чат (1)", "Подключили бота, но не зашли в чат (1)"],
        ["https://vk.com/id503", "https://vk.com/id501", "https://vk.com/id502"],
        ["https://vk.com/id504", "", ""],
    ]
    assert sheets_client.column_widths["s1", "Статус"] == [320, 320, 320]


async def test_without_an_access_block_says_so(service, db_session, sheets_client) -> None:
    club = await make_club(db_session, spreadsheet_id="s1", status_sheet_name="Статус")

    await service.publish(club.id)

    assert sheets_client.written["s1", "Статус"] == [[f"Сейчас нет блока с доступом · {TITLE_TAIL}"]]


async def test_write_failure_is_a_domain_error(service, db_session, sheets_client) -> None:
    club = await make_club(db_session, spreadsheet_id="s1", status_sheet_name="Статус")
    sheets_client.fail("s1", "Статус", SheetsClientError("Google Sheets API error 403 PERMISSION_DENIED"))

    with pytest.raises(StatusSheetWriteError):
        await service.publish(club.id)


async def test_only_active_clubs_with_a_status_sheet_are_listed(service, db_session) -> None:
    club = await make_club(db_session, spreadsheet_id="s1", status_sheet_name="Статус")
    await make_club(db_session, spreadsheet_id="s2", status_sheet_name="Статус", is_active=False)
    await make_club(db_session, spreadsheet_id="s3")

    assert await service.list_club_ids() == [club.id]


async def test_disabled_client_lists_no_clubs(service, db_session, sheets_client) -> None:
    await make_club(db_session, spreadsheet_id="s1", status_sheet_name="Статус")
    sheets_client.is_enabled = False

    assert await service.list_club_ids() == []
