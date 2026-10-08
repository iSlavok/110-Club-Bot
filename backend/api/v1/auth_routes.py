from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Request, Response, status

from api.core.auth import SESSION_COOKIE, require, session_cookie
from api.schemas.auth_schemas import AuthConfigResponse, CurrentAdminResponse, LoginCodeRequest
from app.config import AuthSettings
from app.schemas import AdminPrincipal, SessionGrant, TelegramWidgetPayload
from app.services import AdminSessionService, LoginService

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


def _set_session_cookie(response: Response, grant: SessionGrant, settings: AuthSettings) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        grant.token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        path="/api",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


@router.get("/config")
async def get_auth_config(login_service: FromDishka[LoginService]) -> AuthConfigResponse:
    config = await login_service.get_config()
    return AuthConfigResponse.from_dto(config)


@router.post("/code")
async def login_with_code(
    body: LoginCodeRequest,
    request: Request,
    response: Response,
    login_service: FromDishka[LoginService],
    settings: FromDishka[AuthSettings],
) -> CurrentAdminResponse:
    client_key = request.client.host if request.client else "unknown"
    grant = await login_service.login_with_code(body.code, client_key)
    _set_session_cookie(response, grant, settings)
    return CurrentAdminResponse.from_dto(grant.admin)


@router.post("/widget")
async def login_with_widget(
    payload: TelegramWidgetPayload,
    response: Response,
    login_service: FromDishka[LoginService],
    settings: FromDishka[AuthSettings],
) -> CurrentAdminResponse:
    grant = await login_service.login_with_widget(payload)
    _set_session_cookie(response, grant, settings)
    return CurrentAdminResponse.from_dto(grant.admin)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: Annotated[str | None, Depends(session_cookie)],
    response: Response,
    admin_session_service: FromDishka[AdminSessionService],
) -> None:
    if token:
        await admin_session_service.end(token)
    response.delete_cookie(SESSION_COOKIE, path="/api")


@router.get("/me")
async def get_me(admin: Annotated[AdminPrincipal, require()]) -> CurrentAdminResponse:
    return CurrentAdminResponse.from_dto(admin)
