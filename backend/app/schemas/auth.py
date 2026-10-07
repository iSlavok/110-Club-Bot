from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import Permission


class AdminPrincipal(BaseModel):
    id: int
    tg_id: int
    name: str
    is_owner: bool
    permissions: frozenset[Permission]

    def has(self, permission: Permission) -> bool:
        return permission in self.permissions


class SessionGrant(BaseModel):
    token: str
    expires_at: datetime
    admin: AdminPrincipal


class IssuedLoginCode(BaseModel):
    code: str
    expires_at: datetime


class AuthConfig(BaseModel):
    widget_enabled: bool
    bot_username: str


class TelegramWidgetPayload(BaseModel):
    id: int = Field(description="Telegram user id")
    first_name: str = Field(description="Telegram first name")
    last_name: str | None = Field(default=None, description="Telegram last name")
    username: str | None = Field(default=None, description="Telegram username")
    photo_url: str | None = Field(default=None, description="Avatar URL")
    auth_date: int = Field(description="Unix time of the authorization")
    hash: str = Field(description="HMAC-SHA256 signature from Telegram")

    def signed_fields(self) -> dict[str, object]:
        return self.model_dump(exclude={"hash"}, exclude_none=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}" if self.last_name else self.first_name
