from app.exceptions.base import ConflictError, InvalidInputError, NotFoundError


class ClubNotFoundError(NotFoundError):
    def __init__(self, club_id: int) -> None:
        super().__init__(f"Club {club_id} not found")


class ClubTitleTakenError(ConflictError):
    def __init__(self, title: str) -> None:
        super().__init__(f"Club '{title}' already exists")


class BlockNotFoundError(NotFoundError):
    def __init__(self, block_id: int) -> None:
        super().__init__(f"Block {block_id} not found")


class BlockColumnTakenError(ConflictError):
    def __init__(self, column_title: str) -> None:
        super().__init__(f"Another block of this club already uses sheet column '{column_title}'")


class InvalidBlockPeriodError(InvalidInputError):
    def __init__(self) -> None:
        super().__init__("Block must end after it starts")


class BlockHasMembersError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Block has members from the sheet and cannot be deleted")
