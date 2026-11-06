import pytest

from app.services import StatusSheetService
from tests.factories import make_club
from worker.jobs import publish_status_sheets


@pytest.fixture
async def service(request_container) -> StatusSheetService:
    return await request_container.get(StatusSheetService)


async def test_failed_club_does_not_stop_the_others(container, service, db_session, sheets_client) -> None:
    await make_club(db_session, spreadsheet_id="s1", status_sheet_name="Статус")
    await make_club(db_session, spreadsheet_id="s2", status_sheet_name="Статус")
    sheets_client.fail("s1", "Статус", RuntimeError("bug"))

    await publish_status_sheets(container, service)

    assert list(sheets_client.written) == [("s2", "Статус")]
