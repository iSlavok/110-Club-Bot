from app.repositories import AdminSessionRepository, LoginCodeRepository, VkAuthRequestRepository
from app.utils import Clock


class AuthCleanupService:
    def __init__(
        self,
        admin_session_repository: AdminSessionRepository,
        login_code_repository: LoginCodeRepository,
        vk_auth_request_repository: VkAuthRequestRepository,
        clock: Clock,
    ) -> None:
        self._admin_session_repository = admin_session_repository
        self._login_code_repository = login_code_repository
        self._vk_auth_request_repository = vk_auth_request_repository
        self._clock = clock

    async def purge_expired(self) -> None:
        now = self._clock.now()
        await self._admin_session_repository.delete_expired(now)
        await self._login_code_repository.delete_spent(now)
        await self._vk_auth_request_repository.delete_spent(now)
