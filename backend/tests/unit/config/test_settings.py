import pytest
from pydantic import SecretStr

from app.config import BotSettings, DatabaseSettings, RedisSettings, Settings


def _settings() -> Settings:
    return Settings(
        db=DatabaseSettings(name="club", user="club", password=SecretStr("secret")),
        redis=RedisSettings(password=SecretStr("secret")),
        bot=BotSettings(token=SecretStr("123:token")),
    )


@pytest.mark.parametrize(("raw", "expected"), [("", None), ("-1001234", -1001234)])
def test_alerts_chat_id_from_env(monkeypatch, raw: str, expected: int | None) -> None:
    monkeypatch.setenv("ALERTS_CHAT_ID", raw)

    assert _settings().alerts.chat_id == expected
