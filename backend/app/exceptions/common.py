from app.exceptions.base import InvalidInputError


class EmptyUpdateError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__("Nothing to update")
