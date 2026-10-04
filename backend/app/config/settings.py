from pydantic import BaseModel, SecretStr
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


class LogSettings(BaseModel):
    level: str = "INFO"


class Settings(BaseSettings):
    # DB_HOST -> db.host: one "_" split keeps field names with underscores intact (DB_POOL_SIZE -> db.pool_size).
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1, extra="ignore")

    db: DatabaseSettings
    redis: RedisSettings
    bot: BotSettings
    api: ApiSettings = ApiSettings()
    log: LogSettings = LogSettings()
