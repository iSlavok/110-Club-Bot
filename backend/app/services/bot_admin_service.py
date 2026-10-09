from app.repositories import AdminUserRepository
from app.services.admin_access_resolver import AdminAccessResolver


class BotAdminService:
    def __init__(self, admin_user_repository: AdminUserRepository, access_resolver: AdminAccessResolver) -> None:
        self._admin_user_repository = admin_user_repository
        self._access_resolver = access_resolver

    # Owners may have no admin_users row until their first login.
    async def is_admin(self, tg_id: int) -> bool:
        if self._access_resolver.is_owner(tg_id):
            return True
        admin = await self._admin_user_repository.get_by_tg_id(tg_id)
        return admin is not None and self._access_resolver.resolve(admin) is not None
