from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import BlockMemberSort, BlockMemberState, ChatAccessStatus, SortOrder
from app.schemas import BlockDTO, BlockMember, BlockMemberFunnel, BlockMemberUser, BlockSummary, ClubDTO, PageParams
from app.schemas.club_schemas import STATUS_SHEET_DESCRIPTION


class ClubResponse(BaseModel):
    id: int = Field(description="Club id")
    title: str = Field(description="Unique club name")
    chat_id: int | None = Field(description="Telegram id of the club chat")
    reminders_topic_id: int | None = Field(description="Forum topic id for reminders")
    spreadsheet_id: str | None = Field(description="Google Sheets document id")
    sheet_name: str | None = Field(description="Sheet with block columns")
    status_sheet_name: str | None = Field(description=STATUS_SHEET_DESCRIPTION)
    is_active: bool = Field(description="Inactive clubs are skipped by the bot")
    hide_service_messages: bool = Field(description="Bot deletes the join and leave messages in the club chat")

    @classmethod
    def from_dto(cls, club: ClubDTO) -> Self:
        return cls(
            id=club.id,
            title=club.title,
            chat_id=club.chat_id,
            reminders_topic_id=club.reminders_topic_id,
            spreadsheet_id=club.spreadsheet_id,
            sheet_name=club.sheet_name,
            status_sheet_name=club.status_sheet_name,
            is_active=club.is_active,
            hide_service_messages=club.hide_service_messages,
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


class BlockMemberFilters(BaseModel):
    state: BlockMemberState | None = Field(
        default=None,
        description=(
            "in_chat: joined the club chat; not_in_chat: everyone else; "
            "no_bot: never linked the bot; not_joined: linked the bot but not in the chat"
        ),
    )
    q: str | None = Field(default=None, max_length=100, description="Name, username, Telegram or VK id")


class BlockMemberListParams(PageParams, BlockMemberFilters):
    sort: BlockMemberSort = Field(
        default=BlockMemberSort.BOT,
        description=(
            "vk: by VK id; bot: linked the bot first, by name; chat: in the chat first, then invited, left, removed"
        ),
    )
    order: SortOrder = Field(default=SortOrder.ASC, description="desc reverses the sort")


class BlockMemberUserResponse(BaseModel):
    id: int = Field(description="User id")
    full_name: str = Field(description="Telegram display name")
    tg_username: str | None = Field(description="Telegram username without @")
    chat_status: ChatAccessStatus | None = Field(
        description="State in the club chat for students the bot invited; null if the bot never invited them",
    )
    chat_joined_at: datetime | None = Field(description="When the student last joined the club chat")

    @classmethod
    def from_dto(cls, user: BlockMemberUser) -> Self:
        return cls(
            id=user.id,
            full_name=user.full_name,
            tg_username=user.tg_username,
            chat_status=user.chat_status,
            chat_joined_at=user.chat_joined_at,
        )


class BlockMemberResponse(BaseModel):
    vk_id: int = Field(description="VK id from the sheet")
    user: BlockMemberUserResponse | None = Field(description="Bot user who linked this VK profile, if any")

    @classmethod
    def from_dto(cls, member: BlockMember) -> Self:
        return cls(
            vk_id=member.vk_id,
            user=None if member.user is None else BlockMemberUserResponse.from_dto(member.user),
        )


class BlockMemberFunnelResponse(BaseModel):
    total: int = Field(description="Members of the block in the sheet")
    with_bot: int = Field(description="Members who linked the bot")
    in_chat: int = Field(description="Members in the club chat")

    @classmethod
    def from_dto(cls, funnel: BlockMemberFunnel) -> Self:
        return cls(total=funnel.total, with_bot=funnel.with_bot, in_chat=funnel.in_chat)
