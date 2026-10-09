from datetime import UTC, datetime

import pytest

from app.clients import SheetsClientError
from app.enums import Permission, SheetIssueKind, SheetSyncStatus
from tests.factories import make_admin_user, make_block, make_club, make_role, make_sheet_sync

P = Permission


@pytest.fixture
async def club(db_session):
    return await make_club(db_session, spreadsheet_id="s1", sheet_name="list")


@pytest.fixture
async def syncer(db_session):
    return await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW, P.SYNC_RUN))


@pytest.fixture
async def block(db_session, club):
    return await make_block(db_session, club, sheet_column_title="Блок 5")


@pytest.mark.usefixtures("block")
async def test_manual_sync_returns_its_result(api_client, login_as, syncer, club, sheets_client) -> None:
    sheets_client.set_sheet("s1", "list", [[True, "Блок 5", 501, "x"]])
    await login_as(syncer)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert (body["added"], body["removal_requested"]) == (1, 0)
    assert body["issues"] == [{"kind": "invalid_value", "column": "Блок 5", "row": 4, "value": "x"}]
    assert body["error"] is None


async def test_failed_sheet_read_is_a_result_not_an_error(api_client, login_as, syncer, club, sheets_client) -> None:
    sheets_client.fail("s1", "list", SheetsClientError("Google Sheets API error 404 NOT_FOUND"))
    await login_as(syncer)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/sync")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error"] == "Google Sheets API error 404 NOT_FOUND"


async def test_sync_needs_permission(api_client, login_as, db_session, club) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW, P.CLUBS_EDIT)))

    response = await api_client.post(f"/api/v1/clubs/{club.id}/sync")

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


async def test_club_without_sheet_is_rejected(api_client, login_as, syncer, db_session) -> None:
    club = await make_club(db_session)
    await login_as(syncer)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/sync")

    assert response.status_code == 409
    assert response.json()["code"] == "CLUB_NOT_SYNCABLE"


async def test_disabled_sync_is_reported(api_client, login_as, syncer, club, sheets_client) -> None:
    sheets_client.is_enabled = False
    await login_as(syncer)

    response = await api_client.post(f"/api/v1/clubs/{club.id}/sync")

    assert response.status_code == 502
    assert response.json()["code"] == "SHEET_SYNC_DISABLED"


async def test_unknown_club_sync_is_404(api_client, login_as, syncer) -> None:
    await login_as(syncer)

    response = await api_client.post("/api/v1/clubs/999999/sync")

    assert response.status_code == 404
    assert response.json()["code"] == "CLUB_NOT_FOUND"


async def test_history_is_newest_first_with_issues(api_client, login_as, db_session, club) -> None:
    issue = {"kind": SheetIssueKind.UNKNOWN_COLUMN, "column": "Блок 9", "row": None, "value": None}
    await make_sheet_sync(db_session, club, started_at=datetime(2026, 10, 1, 8, 0, tzinfo=UTC))
    await make_sheet_sync(
        db_session,
        club,
        started_at=datetime(2026, 10, 1, 8, 10, tzinfo=UTC),
        status=SheetSyncStatus.FAILED,
        error="boom",
    )
    await make_sheet_sync(db_session, club, started_at=datetime(2026, 10, 1, 8, 20, tzinfo=UTC), issues=[issue])
    await make_sheet_sync(db_session, await make_club(db_session))
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW)))

    response = await api_client.get(f"/api/v1/clubs/{club.id}/syncs", params={"per_page": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 3
    assert [item["started_at"] for item in body["items"]] == ["2026-10-01T08:20:00Z", "2026-10-01T08:10:00Z"]
    assert body["items"][0]["issues"] == [{"kind": "unknown_column", "column": "Блок 9", "row": None, "value": None}]
    assert body["items"][1]["status"] == "failed"
    assert body["items"][1]["error"] == "boom"


async def test_history_of_unknown_club_is_404(api_client, login_as, syncer) -> None:
    await login_as(syncer)

    response = await api_client.get("/api/v1/clubs/999999/syncs")

    assert response.status_code == 404
    assert response.json()["code"] == "CLUB_NOT_FOUND"
