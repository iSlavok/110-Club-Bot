from typing import Annotated

from pydantic import BaseModel, SecretStr, StringConstraints, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DatabaseSettings(BaseModel):
    host: str = "postgres"
    port: int = 5432
    name: str
    user: str
    password: SecretStr
    pool_size: int = 10
    max_overflow: int = 10

    @property
    def url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
        )


class RedisSettings(BaseModel):
    host: str = "redis"
    port: int = 6379
    password: SecretStr
    db: int = 0


class BotSettings(BaseModel):
    token: SecretStr


class ApiSettings(BaseModel):
    host: str = "0.0.0.0"  # noqa: S104 - binds inside the container, published only via the reverse proxy
    port: int = 8000


class AuthSettings(BaseModel):
    owner_ids: list[int] = []
    widget_enabled: bool = False
    cookie_secure: bool = True
    session_ttl_days: int = 30


class PublicSettings(BaseModel):
    url: Annotated[str, StringConstraints(pattern=r"^https?://[^\s/]+(/\S*)?$")] | None = None

    @field_validator("url", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value

    # Without the trailing slash, so callers join paths as f"{url}/api/v1/...".
    @field_validator("url")
    @classmethod
    def _strip_trailing_slash(cls, value: str | None) -> str | None:
        return value.rstrip("/") if value is not None else None


class AlertsSettings(BaseModel):
    chat_id: int | None = None

    # An empty ALERTS_CHAT_ID= in .env means "not set", not a parse error.
    @field_validator("chat_id", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value


class LogSettings(BaseModel):
    level: str = "INFO"


class Settings(BaseSettings):
    # DB_HOST -> db.host: one "_" split keeps field names with underscores intact (DB_POOL_SIZE -> db.pool_size).
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1, extra="ignore")

    db: DatabaseSettings
    redis: RedisSettings
    bot: BotSettings
    api: ApiSettings = ApiSettings()
    public: PublicSettings = PublicSettings()
    auth: AuthSettings = AuthSettings()
    alerts: AlertsSettings = AlertsSettings()
    log: LogSettings = LogSettings()
