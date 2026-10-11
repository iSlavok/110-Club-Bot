from collections.abc import Iterable

from app.enums import Permission
from app.exceptions import PermissionEscalationError
from app.schemas import AdminPrincipal


# Without this an admin with roles.edit or admins.edit could grant themselves every permission.
def ensure_within_own_permissions(actor: AdminPrincipal, permissions: Iterable[Permission]) -> None:
    if not actor.is_owner and not actor.permissions.issuperset(permissions):
        raise PermissionEscalationError
