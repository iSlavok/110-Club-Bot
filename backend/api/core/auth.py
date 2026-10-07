from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, params
from fastapi.security import APIKeyCookie

from app.enums import Permission
from app.exceptions import PermissionDeniedError
from app.schemas import AdminPrincipal
from app.services import AdminSessionService

SESSION_COOKIE = "club110_session"

session_cookie = APIKeyCookie(name=SESSION_COOKIE, auto_error=False)


@inject
async def _get_current_admin(
    token: Annotated[str | None, Depends(session_cookie)],
    admin_session_service: FromDishka[AdminSessionService],
) -> AdminPrincipal:
    return await admin_session_service.authenticate(token)


# One form everywhere: dependencies=[require(...)] to guard a route,
# Annotated[AdminPrincipal, require(...)] when the route needs the admin. No permission = any logged-in admin.
def require(permission: Permission | None = None) -> params.Depends:
    async def guard(admin: Annotated[AdminPrincipal, Depends(_get_current_admin)]) -> AdminPrincipal:
        if permission is not None and not admin.has(permission):
            raise PermissionDeniedError
        return admin

    return Depends(guard)
