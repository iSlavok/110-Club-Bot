from app.exceptions.base import ConflictError, ExternalServiceError, InvalidInputError, NotFoundError


class UserNotRegisteredError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("User has not started the bot yet")


class VkAlreadyLinkedError(ConflictError):
    def __init__(self) -> None:
        super().__init__("VK is already linked to this Telegram account")


class VkAccountTakenError(ConflictError):
    def __init__(self) -> None:
        super().__init__("This VK profile is linked to another Telegram account")


class InvalidVkLinkError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__("Not a link to a VK profile")


class VkProfileNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("VK profile not found or deleted")


class VkLinkModeChangedError(ConflictError):
    def __init__(self) -> None:
        super().__init__("VK link mode has changed, start linking again")


class VkLinkUnavailableError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("VK linking is not configured on the server")


class VkUnavailableError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("VK is not reachable right now")
