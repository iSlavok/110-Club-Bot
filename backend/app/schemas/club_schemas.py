from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import AfterValidator, AwareDatetime, BaseModel, Field, StringConstraints, model_validator

from app.models import Block, Club
from app.models.club import CLUB_TEXT_MAX_LEN
from app.schemas.patch_schemas import Maybe, PatchSchema
from app.types import BigInt, PositiveInt32

# Annotated form, not bare AwareDatetime: the bare class loses its tz check when wrapped in Maybe.
type Moment = Annotated[datetime, AwareDatetime, AfterValidator(lambda value: value.astimezone(UTC))]
type ClubText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CLUB_TEXT_MAX_LEN)]


class ClubDTO(BaseModel):
    id: int
    title: str
    chat_id: int | None
    reminders_topic_id: int | None
    spreadsheet_id: str | None
    sheet_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, club: Club) -> Self:
        return cls(
            id=club.id,
            title=club.title,
            chat_id=club.chat_id,
            reminders_topic_id=club.reminders_topic_id,
            spreadsheet_id=club.spreadsheet_id,
            sheet_name=club.sheet_name,
            is_active=club.is_active,
            created_at=club.created_at,
            updated_at=club.updated_at,
        )


class ClubCreate(BaseModel):
    title: ClubText = Field(description="Unique club name")
    chat_id: BigInt | None = Field(default=None, description="Telegram id of the club chat")
    reminders_topic_id: PositiveInt32 | None = Field(default=None, description="Forum topic id for reminders")
    spreadsheet_id: ClubText | None = Field(default=None, description="Google Sheets document id")
    sheet_name: ClubText | None = Field(default=None, description="Sheet with block columns")


class ClubUpdate(PatchSchema):
    title: Maybe[ClubText] = Field(description="Unique club name")
    chat_id: Maybe[BigInt | None] = Field(description="Telegram id of the club chat")
    reminders_topic_id: Maybe[PositiveInt32 | None] = Field(description="Forum topic id for reminders")
    spreadsheet_id: Maybe[ClubText | None] = Field(description="Google Sheets document id")
    sheet_name: Maybe[ClubText | None] = Field(description="Sheet with block columns")
    is_active: Maybe[bool] = Field(description="Inactive clubs are skipped by the bot")


class BlockDTO(BaseModel):
    id: int
    club_id: int
    title: str
    sheet_column_title: str
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, block: Block) -> Self:
        return cls(
            id=block.id,
            club_id=block.club_id,
            title=block.title,
            sheet_column_title=block.sheet_column_title,
            starts_at=block.starts_at,
            ends_at=block.ends_at,
            created_at=block.created_at,
            updated_at=block.updated_at,
        )


class BlockSummary(BaseModel):
    block: BlockDTO
    members_count: int


class BlockMemberUser(BaseModel):
    id: int
    full_name: str
    tg_username: str | None


class BlockMember(BaseModel):
    vk_id: int
    user: BlockMemberUser | None


class BlockCreate(BaseModel):
    title: ClubText = Field(description="Block name shown to admins")
    sheet_column_title: ClubText = Field(description="Header of the sheet column with this block's members")
    starts_at: Moment = Field(description="Block start")
    ends_at: Moment = Field(description="Block end, after the start")

    @model_validator(mode="after")
    def _ends_after_start(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class BlockUpdate(PatchSchema):
    title: Maybe[ClubText] = Field(description="Block name shown to admins")
    sheet_column_title: Maybe[ClubText] = Field(description="Header of the sheet column with this block's members")
    starts_at: Maybe[Moment] = Field(description="Block start")
    ends_at: Maybe[Moment] = Field(description="Block end, after the start")
