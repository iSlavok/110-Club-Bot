from app.config import AuthSettings
from app.enums import Permission, known_permissions
from app.models import AdminUser
from app.schemas import AdminPrincipal


class AdminAccessResolver:
    def __init__(self, settings: AuthSettings) -> None:
        self._owner_ids = frozenset(settings.owner_ids)

    def is_owner(self, tg_id: int) -> bool:
        return tg_id in self._owner_ids

    # The admin's role must be loaded. None means the account may not use the admin panel.
    def resolve(self, admin: AdminUser) -> AdminPrincipal | None:
        if self.is_owner(admin.tg_id):
            permissions = frozenset(Permission)
        elif admin.is_active and admin.role is not None:
            permissions = known_permissions(admin.role.permissions)
        else:
            return None
        return AdminPrincipal(
            id=admin.id,
            tg_id=admin.tg_id,
            name=admin.name,
            is_owner=self.is_owner(admin.tg_id),
            permissions=permissions,
        )
