from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RemovalRequestStatus
from app.models import Block, Club, MembershipRemovalItem, MembershipRemovalRequest, User
from app.queries.rows import RemovalCandidateRow, RemovalRequestRow


class MembershipRemovalQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_request(self, request_id: int) -> RemovalRequestRow | None:
        statement = (
            select(
                MembershipRemovalRequest.id,
                Club.id,
                Club.title,
                Block.id,
                Block.title,
                MembershipRemovalRequest.status,
                MembershipRemovalRequest.alert_message_id,
                MembershipRemovalRequest.created_at,
            )
            .join(Block, Block.id == MembershipRemovalRequest.block_id)
            .join(Club, Club.id == Block.club_id)
            .where(MembershipRemovalRequest.id == request_id)
        )
        result = await self._session.execute(statement)
        row = result.one_or_none()
        if row is None:
            return None
        id_, club_id, club_title, block_id, block_title, status, alert_message_id, created_at = row
        return RemovalRequestRow(
            id=id_,
            club_id=club_id,
            club_title=club_title,
            block_id=block_id,
            block_title=block_title,
            status=status,
            alert_message_id=alert_message_id,
            created_at=created_at,
        )

    # users.vk_id is unique, so the outer join never multiplies items.
    async def list_candidates(self, request_id: int) -> list[RemovalCandidateRow]:
        statement = (
            select(MembershipRemovalItem.vk_id, User.full_name, User.tg_username)
            .outerjoin(User, User.vk_id == MembershipRemovalItem.vk_id)
            .where(MembershipRemovalItem.request_id == request_id)
            .order_by(MembershipRemovalItem.vk_id)
        )
        result = await self._session.execute(statement)
        return [
            RemovalCandidateRow(vk_id=vk_id, full_name=full_name, tg_username=tg_username)
            for vk_id, full_name, tg_username in result
        ]

    async def count_pending_for_club(self, club_id: int) -> int:
        statement = (
            select(func.count(MembershipRemovalRequest.id))
            .select_from(MembershipRemovalRequest)
            .join(Block, Block.id == MembershipRemovalRequest.block_id)
            .where(
                Block.club_id == club_id,
                MembershipRemovalRequest.status == RemovalRequestStatus.PENDING,
            )
        )
        return await self._session.scalar(statement) or 0
