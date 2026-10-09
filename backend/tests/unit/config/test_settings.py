import pytest
from pydantic import SecretStr, ValidationError

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


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", None),
        ("https://club.example.com", "https://club.example.com"),
        ("https://club.example.com/", "https://club.example.com"),
        ("http://localhost:8080", "http://localhost:8080"),
    ],
)
def test_public_url_from_env(monkeypatch, raw: str, expected: str | None) -> None:
    monkeypatch.setenv("PUBLIC_URL", raw)

    assert _settings().public.url == expected


@pytest.mark.parametrize("raw", ["club.example.com", "ftp://club.example.com", "https://"])
def test_public_url_must_be_http(monkeypatch, raw: str) -> None:
    monkeypatch.setenv("PUBLIC_URL", raw)

    with pytest.raises(ValidationError):
        _settings()
