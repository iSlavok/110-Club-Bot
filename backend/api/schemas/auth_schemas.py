from typing import Self

from pydantic import BaseModel, Field

from app.enums import Permission
from app.schemas import AdminPrincipal, AuthConfig
from app.utils import LOGIN_CODE_DIGITS


class AuthConfigResponse(BaseModel):
    widget_enabled: bool = Field(description="Whether the Telegram Login Widget is available")
    bot_username: str = Field(description="Bot username without @, used for the widget and the /login hint")

    @classmethod
    def from_dto(cls, config: AuthConfig) -> Self:
        return cls(widget_enabled=config.widget_enabled, bot_username=config.bot_username)


class LoginCodeRequest(BaseModel):
    code: str = Field(pattern=rf"^\d{{{LOGIN_CODE_DIGITS}}}$", description="One-time code the bot sent on /login")


class CurrentAdminResponse(BaseModel):
    id: int = Field(description="Admin account id")
    tg_id: int = Field(description="Telegram user id")
    name: str = Field(description="Display name")
    is_owner: bool = Field(description="Owner from server config: has every permission, cannot be edited")
    permissions: list[Permission] = Field(description="Effective permissions")

    @classmethod
    def from_dto(cls, principal: AdminPrincipal) -> Self:
        return cls(
            id=principal.id,
            tg_id=principal.tg_id,
            name=principal.name,
            is_owner=principal.is_owner,
            permissions=sorted(principal.permissions),
        )
