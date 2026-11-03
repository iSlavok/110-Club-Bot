from app.config import AuthSettings
from app.enums import Permission
from app.repositories import AdminUserRepository, ClubRepository
from app.services.admin_access_resolver import AdminAccessResolver
from app.telegram import CommandMenu


class BotAdminService:
    def __init__(
        self,
        admin_user_repository: AdminUserRepository,
        club_repository: ClubRepository,
        access_resolver: AdminAccessResolver,
        command_menu: CommandMenu,
        auth_settings: AuthSettings,
    ) -> None:
        self._admin_user_repository = admin_user_repository
        self._club_repository = club_repository
        self._access_resolver = access_resolver
        self._command_menu = command_menu
        self._owner_ids = auth_settings.owner_ids

    # Owners may have no admin_users row until their first login.
    async def is_admin(self, tg_id: int) -> bool:
        if self._access_resolver.is_owner(tg_id):
            return True
        admin = await self._admin_user_repository.get_by_tg_id(tg_id)
        return admin is not None and self._access_resolver.resolve(admin) is not None

    async def has_permission(self, tg_id: int, permission: Permission) -> bool:
        if self._access_resolver.is_owner(tg_id):
            return True
        admin = await self._admin_user_repository.get_by_tg_id(tg_id)
        principal = None if admin is None else self._access_resolver.resolve(admin)
        return principal is not None and permission in principal.permissions

    # Who was shown the admin menu is not stored: every account in admin_users that lost access gets it removed.
    async def sync_command_menus(self) -> None:
        await self._command_menu.set_default()
        admin_tg_ids, former_admin_tg_ids = await self._split_admins()
        chat_ids = await self._club_chat_ids()
        for tg_id in sorted(admin_tg_ids):
            await self._show_menus(tg_id, chat_ids)
        for tg_id in sorted(former_admin_tg_ids):
            await self._hide_menus(tg_id, chat_ids)

    # Telegram refuses a per-chat menu until the user has written to the bot, so /start retries it.
    async def sync_command_menu(self, tg_id: int) -> None:
        if await self.is_admin(tg_id):
            await self._command_menu.show_admin(tg_id)

    async def show_admin_menus(self, tg_id: int) -> None:
        chat_ids = await self._club_chat_ids()
        await self._show_menus(tg_id, chat_ids)

    async def hide_admin_menus(self, tg_id: int) -> None:
        chat_ids = await self._club_chat_ids()
        await self._hide_menus(tg_id, chat_ids)

    async def show_chat_menus(self, chat_id: int) -> None:
        admin_tg_ids, _ = await self._split_admins()
        for tg_id in sorted(admin_tg_ids):
            await self._command_menu.show_chat_admin(chat_id, tg_id)

    async def _split_admins(self) -> tuple[set[int], set[int]]:
        admin_tg_ids = set(self._owner_ids)
        former_admin_tg_ids: set[int] = set()
        admins = await self._admin_user_repository.list_all()
        for admin in admins:
            if self._access_resolver.resolve(admin) is None:
                former_admin_tg_ids.add(admin.tg_id)
            else:
                admin_tg_ids.add(admin.tg_id)
        return admin_tg_ids, former_admin_tg_ids

    async def _club_chat_ids(self) -> list[int]:
        clubs = await self._club_repository.list_with_chat()
        return sorted({club.chat_id for club in clubs if club.chat_id is not None})

    async def _show_menus(self, tg_id: int, chat_ids: list[int]) -> None:
        await self._command_menu.show_admin(tg_id)
        for chat_id in chat_ids:
            await self._command_menu.show_chat_admin(chat_id, tg_id)

    async def _hide_menus(self, tg_id: int, chat_ids: list[int]) -> None:
        await self._command_menu.hide_admin(tg_id)
        for chat_id in chat_ids:
            await self._command_menu.hide_chat_admin(chat_id, tg_id)
