from pydantic import BaseModel

from app.schemas.vk_link_schemas import ClubAccess


class StudentClubStatus(BaseModel):
    # access.invite_link is set only while the student is not in the chat.
    access: ClubAccess
    # None when the club has no chat.
    in_chat: bool | None
    # Set only while a block runs and the student is already listed for the next one.
    next_block_title: str | None


class StudentStatus(BaseModel):
    vk_id: int | None
    clubs: list[StudentClubStatus]
