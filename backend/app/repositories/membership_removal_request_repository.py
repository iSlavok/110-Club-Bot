from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository
from app.models import MembershipRemovalRequest


class MembershipRemovalRequestRepository(BaseRepository[MembershipRemovalRequest]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MembershipRemovalRequest)
