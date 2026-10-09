from collections.abc import Set

from loguru import logger

from app import texts
from app.enums import Permission, RemovalDecision, RemovalRequestStatus
from app.exceptions import PermissionDeniedError, RemovalRequestDecidedError, RemovalRequestNotFoundError
from app.models import MembershipRemovalRequest
from app.queries import MembershipRemovalQueries
from app.repositories import (
    AdminUserRepository,
    MembershipRemovalItemRepository,
    MembershipRemovalRequestRepository,
    MembershipRepository,
    SheetSyncRepository,
)
from app.schemas import RemovalCandidate, RemovalRequestAlert, TelegramProfile
from app.services.admin_access_resolver import AdminAccessResolver
from app.telegram import AdminAlerts, removal_request_keyboard
from app.utils import Clock

# A rejected removal is remembered until the student is back in the sheet, so it is not asked again every sync.
OPEN_STATUSES = (RemovalRequestStatus.PENDING, RemovalRequestStatus.REJECTED)


class MembershipRemovalService:
    def __init__(
        self,
        *,
        request_repository: MembershipRemovalRequestRepository,
        item_repository: MembershipRemovalItemRepository,
        membership_repository: MembershipRepository,
        sheet_sync_repository: SheetSyncRepository,
        admin_user_repository: AdminUserRepository,
        removal_queries: MembershipRemovalQueries,
        access_resolver: AdminAccessResolver,
        admin_alerts: AdminAlerts,
        clock: Clock,
    ) -> None:
        self._request_repository = request_repository
        self._item_repository = item_repository
        self._membership_repository = membership_repository
        self._sheet_sync_repository = sheet_sync_repository
        self._admin_user_repository = admin_user_repository
        self._removal_queries = removal_queries
        self._access_resolver = access_resolver
        self._admin_alerts = admin_alerts
        self._clock = clock

    # Runs under the club's sync lock. Returns how many members were newly sent for confirmation.
    async def reconcile_block(self, block_id: int, *, members: Set[int], wanted: Set[int]) -> int:
        open_items = await self._item_repository.list_for_block(block_id=block_id, statuses=OPEN_STATUSES)
        returned = [item for item in open_items if item.vk_id in wanted]
        await self._item_repository.delete_many([item.id for item in returned])
        shrunk = {item.request_id for item in returned if item.request.status is RemovalRequestStatus.PENDING}
        for request_id in sorted(shrunk):
            await self._refresh_pending(request_id)

        asked = {item.vk_id for item in open_items}
        gone = members - wanted - asked
        if gone:
            await self._open_request(block_id, gone)
        return len(gone)

    async def decide(
        self, request_id: int, decision: RemovalDecision, decider: TelegramProfile
    ) -> RemovalRequestStatus:
        found = await self._removal_queries.get_request(request_id)
        if found is None:
            raise RemovalRequestNotFoundError(request_id)
        await self._ensure_can_decide(decider.tg_id)
        # Same lock as the sync: a decision and a sync of the club never change one request at once.
        await self._sheet_sync_repository.lock_club(found.club_id)
        request = await self._request_repository.get_by_id(request_id)
        if request is None:
            raise RemovalRequestNotFoundError(request_id)
        if request.status is not RemovalRequestStatus.PENDING:
            raise RemovalRequestDecidedError(request_id)

        if decision is RemovalDecision.CONFIRM:
            vk_ids = await self._item_repository.list_vk_ids(request_id)
            await self._membership_repository.delete_many(block_id=request.block_id, vk_ids=vk_ids)
            request.status = RemovalRequestStatus.CONFIRMED
        else:
            request.status = RemovalRequestStatus.REJECTED
        request.decided_by_tg_id = decider.tg_id
        request.decided_at = self._clock.now()
        await self._request_repository.flush()
        logger.info("Removal request {} {} by {}", request_id, request.status, decider.tg_id)

        if request.alert_message_id is not None:
            alert = await self._alert(request, decided_by=decider.full_name)
            await self._admin_alerts.edit(request.alert_message_id, texts.alerts.removal_request(alert))
        return request.status

    async def _open_request(self, block_id: int, vk_ids: Set[int]) -> None:
        request = MembershipRemovalRequest(block_id=block_id, status=RemovalRequestStatus.PENDING)
        self._request_repository.add(request)
        await self._request_repository.flush()
        await self._item_repository.add_many(request_id=request.id, vk_ids=vk_ids)
        alert = await self._alert(request)
        request.alert_message_id = await self._admin_alerts.send(
            texts.alerts.removal_request(alert),
            removal_request_keyboard(request.id),
        )

    async def _refresh_pending(self, request_id: int) -> None:
        request = await self._request_repository.get_by_id(request_id)
        if request is None:
            return
        remaining = await self._item_repository.list_vk_ids(request_id)
        if not remaining:
            request.status = RemovalRequestStatus.CANCELLED
            request.decided_at = self._clock.now()
        if request.alert_message_id is None:
            return
        alert = await self._alert(request)
        keyboard = removal_request_keyboard(request_id) if remaining else None
        await self._admin_alerts.edit(request.alert_message_id, texts.alerts.removal_request(alert), keyboard)

    async def _alert(self, request: MembershipRemovalRequest, *, decided_by: str | None = None) -> RemovalRequestAlert:
        found = await self._removal_queries.get_request(request.id)
        if found is None:
            raise RemovalRequestNotFoundError(request.id)
        candidates = await self._removal_queries.list_candidates(request.id)
        return RemovalRequestAlert(
            club_title=found.club_title,
            block_title=found.block_title,
            status=request.status,
            created_at=request.created_at,
            candidates=[
                RemovalCandidate(vk_id=row.vk_id, full_name=row.full_name, tg_username=row.tg_username)
                for row in candidates
            ],
            decided_by=decided_by,
            decided_at=request.decided_at,
        )

    async def _ensure_can_decide(self, tg_id: int) -> None:
        if self._access_resolver.is_owner(tg_id):
            return
        admin = await self._admin_user_repository.get_by_tg_id(tg_id)
        principal = self._access_resolver.resolve(admin) if admin is not None else None
        if principal is None or not principal.has(Permission.SYNC_RUN):
            raise PermissionDeniedError
