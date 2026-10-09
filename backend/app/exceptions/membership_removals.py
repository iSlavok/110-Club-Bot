from app.exceptions.base import ConflictError, NotFoundError


class RemovalRequestNotFoundError(NotFoundError):
    def __init__(self, request_id: int) -> None:
        super().__init__(f"Membership removal request {request_id} not found")


class RemovalRequestDecidedError(ConflictError):
    def __init__(self, request_id: int) -> None:
        super().__init__(f"Membership removal request {request_id} is already decided or cancelled")
