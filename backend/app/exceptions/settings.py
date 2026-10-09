from app.enums import VkLinkMode
from app.exceptions.base import InvalidInputError, NotFoundError


class AppSettingsMissingError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Bot settings row is missing; run the database migrations")


class VkLinkModeNotConfiguredError(InvalidInputError):
    def __init__(self, mode: VkLinkMode) -> None:
        super().__init__(f"VK link mode '{mode}' is not configured on the server")
