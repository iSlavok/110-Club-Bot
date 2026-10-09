from app.config import AuthSettings
from app.repositories import AdminUserRepository
from app.services.admin_access_resolver import AdminAccessResolver
from app.telegram import CommandMenu


class BotAdminService:
    def __init__(
        self,
        admin_user_repository: AdminUserRepository,
        access_resolver: AdminAccessResolver,
        command_menu: CommandMenu,
        auth_settings: AuthSettings,
    ) -> None:
        self._admin_user_repository = admin_user_repository
        self._access_resolver = access_resolver
        self._command_menu = command_menu
        self._owner_ids = auth_settings.owner_ids

    # Owners may have no admin_users row until their first login.
    async def is_admin(self, tg_id: int) -> bool:
        if self._access_resolver.is_owner(tg_id):
            return True
        admin = await self._admin_user_repository.get_by_tg_id(tg_id)
        return admin is not None and self._access_resolver.resolve(admin) is not None

    # Who was shown the admin menu is not stored: every account in admin_users that lost access gets it removed.
    async def sync_command_menus(self) -> None:
        await self._command_menu.set_default()
        admin_tg_ids = set(self._owner_ids)
        former_admin_tg_ids: set[int] = set()
        admins = await self._admin_user_repository.list_all()
        for admin in admins:
            if self._access_resolver.resolve(admin) is None:
                former_admin_tg_ids.add(admin.tg_id)
            else:
                admin_tg_ids.add(admin.tg_id)
        for tg_id in sorted(admin_tg_ids):
            await self._command_menu.show_admin(tg_id)
        for tg_id in sorted(former_admin_tg_ids):
            await self._command_menu.hide_admin(tg_id)

    # Telegram refuses a per-chat menu until the user has written to the bot, so /start retries it.
    async def sync_command_menu(self, tg_id: int) -> None:
        if await self.is_admin(tg_id):
            await self._command_menu.show_admin(tg_id)
