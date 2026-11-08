import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Protocol
from urllib.parse import quote

import httpx
import requests
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import Request as AuthRequest
from google.auth.transport.requests import Request as RequestsAuthRequest
from google.oauth2 import service_account
from loguru import logger
from pydantic import BaseModel, ValidationError

from app.clients.exceptions import SheetsClientError, SheetsNotConfiguredError
from app.config import GoogleSettings

SHEETS_API_URL = "https://sheets.googleapis.com/v4/spreadsheets"
# Read and write: the bot rewrites the status sheet; it never writes to the sheets curators edit.
SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
REQUEST_TIMEOUT_SECONDS = 30.0

# What values.get returns with UNFORMATTED_VALUE: checkboxes as bool, numbers as int/float, empty cells as "".
type CellValue = bool | int | float | str
type WrittenCell = int | str


class SheetsClient(Protocol):
    @property
    def is_enabled(self) -> bool: ...

    # One inner list per sheet column, top to bottom; trailing empty cells and columns are omitted by the API.
    async def get_columns(self, spreadsheet_id: str, sheet_name: str) -> list[list[CellValue]]: ...

    # Creates the sheet if missing and replaces all its values; rows go top to bottom, widths are pixels from column A.
    async def replace_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        rows: list[list[WrittenCell]],
        *,
        column_widths: Sequence[int] = (),
    ) -> None: ...


class _ValueRange(BaseModel):
    values: list[list[CellValue]] = []


class _SheetProperties(BaseModel):
    sheetId: int  # noqa: N815 - Google API field name
    title: str


class _Sheet(BaseModel):
    properties: _SheetProperties


class _Spreadsheet(BaseModel):
    sheets: list[_Sheet] = []


class _AddSheetReply(BaseModel):
    addSheet: _Sheet  # noqa: N815 - Google API field name


class _BatchUpdateResponse(BaseModel):
    replies: list[_AddSheetReply]


class _ApiError(BaseModel):
    code: int
    message: str = ""
    status: str = ""


class _ApiErrorEnvelope(BaseModel):
    error: _ApiError


class GoogleSheetsClient:
    def __init__(self, credentials: Credentials, auth_request: AuthRequest, http: httpx.AsyncClient) -> None:
        self._credentials = credentials
        self._auth_request = auth_request
        self._http = http
        self._refresh_lock = asyncio.Lock()

    @property
    def is_enabled(self) -> bool:
        return True

    async def get_columns(self, spreadsheet_id: str, sheet_name: str) -> list[list[CellValue]]:
        url = f"{_spreadsheet_url(spreadsheet_id)}/values/{quote(_whole_sheet_range(sheet_name), safe='')}"
        params = {"majorDimension": "COLUMNS", "valueRenderOption": "UNFORMATTED_VALUE"}
        response = await self._request("GET", url, params=params)
        return _parse(_ValueRange, response).values

    async def replace_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        rows: list[list[WrittenCell]],
        *,
        column_widths: Sequence[int] = (),
    ) -> None:
        sheet_id = await self._ensure_sheet(spreadsheet_id, sheet_name)
        if column_widths:
            await self._set_column_widths(spreadsheet_id, sheet_id, column_widths)
        values_url = f"{_spreadsheet_url(spreadsheet_id)}/values/{quote(_whole_sheet_range(sheet_name), safe='')}"
        await self._request("POST", f"{values_url}:clear")
        await self._request(
            "PUT",
            values_url,
            params={"valueInputOption": "RAW"},
            json={"majorDimension": "ROWS", "values": rows},
        )

    # A new sheet is protected with a warning only: people may still edit it, but are told the bot rewrites it.
    async def _ensure_sheet(self, spreadsheet_id: str, sheet_name: str) -> int:
        url = _spreadsheet_url(spreadsheet_id)
        response = await self._request("GET", url, params={"fields": "sheets.properties(sheetId,title)"})
        for sheet in _parse(_Spreadsheet, response).sheets:
            if sheet.properties.title == sheet_name:
                return sheet.properties.sheetId
        add = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        added = await self._request("POST", f"{url}:batchUpdate", json=add)
        sheet_id = _parse(_BatchUpdateResponse, added).replies[0].addSheet.properties.sheetId
        protect = {
            "requests": [
                {"addProtectedRange": {"protectedRange": {"range": {"sheetId": sheet_id}, "warningOnly": True}}},
            ],
        }
        await self._request("POST", f"{url}:batchUpdate", json=protect)
        return sheet_id

    async def _set_column_widths(self, spreadsheet_id: str, sheet_id: int, widths: Sequence[int]) -> None:
        requests = [
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": index, "endIndex": index + 1},
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                },
            }
            for index, width in enumerate(widths)
        ]
        await self._request("POST", f"{_spreadsheet_url(spreadsheet_id)}:batchUpdate", json={"requests": requests})

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: object = None,
    ) -> httpx.Response:
        token = await self._access_token()
        try:
            response = await self._http.request(
                method,
                url,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError as error:
            raise SheetsClientError(f"Google Sheets API is unreachable: {error!r}") from error
        if response.is_error:
            raise SheetsClientError(_describe_error(response))
        return response

    # google-auth refreshes only through a blocking transport, so the token request runs in a thread.
    async def _access_token(self) -> str:
        async with self._refresh_lock:
            if not self._credentials.valid:
                try:
                    await asyncio.to_thread(self._credentials.refresh, self._auth_request)
                except GoogleAuthError as error:
                    raise SheetsClientError(f"Google authorization failed: {error}") from error
        return str(self._credentials.token)


class DisabledSheetsClient:
    @property
    def is_enabled(self) -> bool:
        return False

    async def get_columns(self, spreadsheet_id: str, sheet_name: str) -> list[list[CellValue]]:  # noqa: ARG002 - SheetsClient signature
        raise SheetsNotConfiguredError

    # Parameters are unused here: only the SheetsClient signature needs them.
    async def replace_sheet(
        self,
        spreadsheet_id: str,  # noqa: ARG002
        sheet_name: str,  # noqa: ARG002
        rows: list[list[WrittenCell]],  # noqa: ARG002
        *,
        column_widths: Sequence[int] = (),  # noqa: ARG002
    ) -> None:
        raise SheetsNotConfiguredError


# A missing or broken key disables the sync instead of failing the whole process: the bot and admin panel still work.
@asynccontextmanager
async def open_sheets_client(settings: GoogleSettings) -> AsyncIterator[SheetsClient]:
    credentials = await _load_credentials(settings)
    if credentials is None:
        yield DisabledSheetsClient()
        return
    with requests.Session() as auth_session:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as http:
            yield GoogleSheetsClient(credentials, RequestsAuthRequest(auth_session), http)


async def _load_credentials(settings: GoogleSettings) -> Credentials | None:
    path = settings.credentials_file
    if path is None:
        logger.warning("GOOGLE_CREDENTIALS_FILE is not set, sheet sync is disabled")
        return None
    try:
        return await asyncio.to_thread(
            service_account.Credentials.from_service_account_file,
            str(path),
            scopes=[SHEETS_SCOPE],
        )
    except (OSError, ValueError) as error:
        logger.warning("Cannot load Google credentials from {}, sheet sync is disabled: {}", path, error)
        return None


def _spreadsheet_url(spreadsheet_id: str) -> str:
    return f"{SHEETS_API_URL}/{quote(spreadsheet_id, safe='')}"


def _parse[T: BaseModel](model: type[T], response: httpx.Response) -> T:
    try:
        return model.model_validate_json(response.content)
    except ValidationError as error:
        raise SheetsClientError("Google Sheets API returned an unexpected response") from error


# Quoted so that names with spaces or punctuation stay one sheet reference; a bare sheet name selects all its cells.
def _whole_sheet_range(sheet_name: str) -> str:
    return "'" + sheet_name.replace("'", "''") + "'"


def _describe_error(response: httpx.Response) -> str:
    try:
        envelope = _ApiErrorEnvelope.model_validate_json(response.content)
    except ValidationError:
        return f"Google Sheets API error {response.status_code}"
    error = envelope.error
    details = ": ".join(part for part in (error.status, error.message) if part)
    return f"Google Sheets API error {error.code} {details}".rstrip()
