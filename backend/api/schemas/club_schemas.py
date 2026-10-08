from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.schemas import BlockDTO, BlockMember, BlockMemberUser, BlockSummary, ClubDTO


class ClubResponse(BaseModel):
    id: int = Field(description="Club id")
    title: str = Field(description="Unique club name")
    chat_id: int | None = Field(description="Telegram id of the club chat")
    reminders_topic_id: int | None = Field(description="Forum topic id for reminders")
    spreadsheet_id: str | None = Field(description="Google Sheets document id")
    sheet_name: str | None = Field(description="Sheet with block columns")
    is_active: bool = Field(description="Inactive clubs are skipped by the bot")

    @classmethod
    def from_dto(cls, club: ClubDTO) -> Self:
        return cls(
            id=club.id,
            title=club.title,
            chat_id=club.chat_id,
            reminders_topic_id=club.reminders_topic_id,
            spreadsheet_id=club.spreadsheet_id,
            sheet_name=club.sheet_name,
            is_active=club.is_active,
        )


class BlockResponse(BaseModel):
    id: int = Field(description="Block id")
    club_id: int = Field(description="Club the block belongs to")
    title: str = Field(description="Block name shown to admins")
    sheet_column_title: str = Field(description="Header of the sheet column with this block's members")
    starts_at: datetime = Field(description="Block start, UTC")
    ends_at: datetime = Field(description="Block end, UTC")

    @classmethod
    def from_dto(cls, block: BlockDTO) -> Self:
        return cls(
            id=block.id,
            club_id=block.club_id,
            title=block.title,
            sheet_column_title=block.sheet_column_title,
            starts_at=block.starts_at,
            ends_at=block.ends_at,
        )


class BlockListItemResponse(BlockResponse):
    members_count: int = Field(description="Members of the block from the sheet, including those awaiting removal")

    @classmethod
    def from_summary(cls, summary: BlockSummary) -> Self:
        block = summary.block
        return cls(
            id=block.id,
            club_id=block.club_id,
            title=block.title,
            sheet_column_title=block.sheet_column_title,
            starts_at=block.starts_at,
            ends_at=block.ends_at,
            members_count=summary.members_count,
        )


class BlockMemberUserResponse(BaseModel):
    id: int = Field(description="User id")
    full_name: str = Field(description="Telegram display name")
    tg_username: str | None = Field(description="Telegram username without @")

    @classmethod
    def from_dto(cls, user: BlockMemberUser) -> Self:
        return cls(id=user.id, full_name=user.full_name, tg_username=user.tg_username)


class BlockMemberResponse(BaseModel):
    vk_id: int = Field(description="VK id from the sheet")
    user: BlockMemberUserResponse | None = Field(description="Bot user who linked this VK profile, if any")

    @classmethod
    def from_dto(cls, member: BlockMember) -> Self:
        return cls(
            vk_id=member.vk_id,
            user=None if member.user is None else BlockMemberUserResponse.from_dto(member.user),
        )
