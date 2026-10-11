import asyncio
from collections.abc import AsyncIterator
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
SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
REQUEST_TIMEOUT_SECONDS = 30.0

# What values.get returns with UNFORMATTED_VALUE: checkboxes as bool, numbers as int/float, empty cells as "".
type CellValue = bool | int | float | str


class SheetsClient(Protocol):
    @property
    def is_enabled(self) -> bool: ...

    # One inner list per sheet column, top to bottom; trailing empty cells and columns are omitted by the API.
    async def get_columns(self, spreadsheet_id: str, sheet_name: str) -> list[list[CellValue]]: ...


class _ValueRange(BaseModel):
    values: list[list[CellValue]] = []


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
        token = await self._access_token()
        sheet_range = quote(_whole_sheet_range(sheet_name), safe="")
        url = f"{SHEETS_API_URL}/{quote(spreadsheet_id, safe='')}/values/{sheet_range}"
        params = {"majorDimension": "COLUMNS", "valueRenderOption": "UNFORMATTED_VALUE"}
        try:
            response = await self._http.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
        except httpx.HTTPError as error:
            raise SheetsClientError(f"Google Sheets API is unreachable: {error!r}") from error
        if response.is_error:
            raise SheetsClientError(_describe_error(response))
        try:
            value_range = _ValueRange.model_validate_json(response.content)
        except ValidationError as error:
            raise SheetsClientError("Google Sheets API returned an unexpected response") from error
        return value_range.values

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
