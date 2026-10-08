import json
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from google.auth.credentials import Credentials
from google.auth.exceptions import RefreshError

from app.clients import GoogleSheetsClient, SheetsClientError, SheetsNotConfiguredError, open_sheets_client
from app.config import GoogleSettings


class StubCredentials(Credentials):
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__()
        self.refreshes = 0
        self._fail = fail

    def refresh(self, request: object) -> None:  # noqa: ARG002 - google-auth signature
        if self._fail:
            raise RefreshError("invalid_grant")
        self.refreshes += 1
        self.token = f"token-{self.refreshes}"


type Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def requests_seen() -> list[httpx.Request]:
    return []


def make_client(handler: Handler, credentials: Credentials | None = None) -> GoogleSheetsClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GoogleSheetsClient(credentials or StubCredentials(), MagicMock(), http)


async def test_reads_whole_sheet_by_columns_unformatted(requests_seen: list[httpx.Request]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        return httpx.Response(200, json={"range": "'Состав'!A1:B4", "values": [[True, "Блок 5", 111, "222"], [False]]})

    client = make_client(handler)

    columns = await client.get_columns("sheet-id", "Состав")

    assert columns == [[True, "Блок 5", 111, "222"], [False]]
    request = requests_seen[0]
    assert request.url.path == "/v4/spreadsheets/sheet-id/values/'Состав'"
    assert request.url.params["majorDimension"] == "COLUMNS"
    assert request.url.params["valueRenderOption"] == "UNFORMATTED_VALUE"
    assert request.headers["Authorization"] == "Bearer token-1"


async def test_quotes_sheet_name_with_apostrophe(requests_seen: list[httpx.Request]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        return httpx.Response(200, json={})

    client = make_client(handler)

    columns = await client.get_columns("sheet-id", "Club's list")

    raw_path = requests_seen[0].url.raw_path.decode()
    assert columns == []
    assert raw_path.startswith("/v4/spreadsheets/sheet-id/values/%27Club%27%27s%20list%27?")


async def test_keeps_number_types() -> None:
    client = make_client(lambda _: httpx.Response(200, content=json.dumps({"values": [[True, 1.5, 2.0, 3]]})))

    columns = await client.get_columns("sheet-id", "list")

    assert columns == [[True, 1.5, 2.0, 3]]
    assert [type(value) for value in columns[0]] == [bool, float, float, int]


async def test_reuses_valid_token() -> None:
    credentials = StubCredentials()
    client = make_client(lambda _: httpx.Response(200, json={}), credentials)

    await client.get_columns("sheet-id", "list")
    await client.get_columns("sheet-id", "list")

    assert credentials.refreshes == 1


async def test_api_error_carries_google_message() -> None:
    body = {"error": {"code": 403, "message": "The caller does not have permission", "status": "PERMISSION_DENIED"}}
    client = make_client(lambda _: httpx.Response(403, json=body))

    with pytest.raises(SheetsClientError) as error:
        await client.get_columns("sheet-id", "list")

    assert error.value.message == "Google Sheets API error 403 PERMISSION_DENIED: The caller does not have permission"


async def test_api_error_without_json_body() -> None:
    client = make_client(lambda _: httpx.Response(503, text="Service Unavailable"))

    with pytest.raises(SheetsClientError) as error:
        await client.get_columns("sheet-id", "list")

    assert error.value.message == "Google Sheets API error 503"


async def test_network_error_becomes_client_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    client = make_client(handler)

    with pytest.raises(SheetsClientError, match="unreachable"):
        await client.get_columns("sheet-id", "list")


async def test_unexpected_payload_becomes_client_error() -> None:
    client = make_client(lambda _: httpx.Response(200, json={"values": [[{"nested": 1}]]}))

    with pytest.raises(SheetsClientError, match="unexpected response"):
        await client.get_columns("sheet-id", "list")


async def test_refresh_failure_becomes_client_error() -> None:
    client = make_client(lambda _: httpx.Response(200, json={}), StubCredentials(fail=True))

    with pytest.raises(SheetsClientError, match="authorization failed"):
        await client.get_columns("sheet-id", "list")


@pytest.mark.parametrize("configured_path", [None, "missing.json"])
async def test_missing_credentials_disable_the_client(tmp_path: Path, configured_path: str | None) -> None:
    settings = GoogleSettings(credentials_file=tmp_path / configured_path if configured_path else None)

    async with open_sheets_client(settings) as client:
        assert not client.is_enabled
        with pytest.raises(SheetsNotConfiguredError):
            await client.get_columns("sheet-id", "list")


async def test_broken_credentials_file_disables_the_client(tmp_path: Path) -> None:
    key_file = tmp_path / "key.json"
    key_file.write_text("{not json")

    async with open_sheets_client(GoogleSettings(credentials_file=key_file)) as client:
        assert not client.is_enabled


def test_empty_setting_means_not_configured() -> None:
    assert GoogleSettings.model_validate({"credentials_file": ""}).credentials_file is None
