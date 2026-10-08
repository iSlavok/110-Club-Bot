from app.exceptions.base import ConflictError, ExternalServiceError


class ClubNotSyncableError(ConflictError):
    def __init__(self, club_id: int) -> None:
        super().__init__(f"Club {club_id} is inactive or has no spreadsheet and sheet name set")


class SheetSyncDisabledError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("Sheet sync is disabled: Google credentials are not configured")
