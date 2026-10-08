# Client failures stay below the service layer: services translate them into domain errors.
class ClientError(Exception):
    pass


class LoginThrottleUnavailableError(ClientError):
    pass


class VkClientError(ClientError):
    def __init__(self, message: str, *, api_code: int | None = None) -> None:
        super().__init__(message)
        self.api_code = api_code


class SheetsClientError(ClientError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SheetsNotConfiguredError(SheetsClientError):
    def __init__(self) -> None:
        super().__init__("Google credentials are not configured")
