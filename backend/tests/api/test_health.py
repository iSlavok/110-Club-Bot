import asyncio
from typing import cast
from unittest.mock import AsyncMock

import pytest
from dishka import AsyncContainer
from redis.asyncio import Redis

from app.services import health_service


@pytest.fixture
async def redis(container: AsyncContainer) -> AsyncMock:
    return cast("AsyncMock", await container.get(Redis))


async def test_livez(api_client) -> None:
    response = await api_client.get("/livez")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz_reports_every_dependency(api_client) -> None:
    response = await api_client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"postgres": "ok", "redis": "ok"}}


async def test_readyz_is_unavailable_when_dependency_fails(api_client, redis: AsyncMock) -> None:
    redis.ping.side_effect = ConnectionError("redis is down")

    response = await api_client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "checks": {"postgres": "ok", "redis": "fail"}}


async def test_readyz_fails_hanging_dependency_by_timeout(
    api_client,
    redis: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_service, "CHECK_TIMEOUT_SECONDS", 0.01)

    async def hang() -> None:
        await asyncio.sleep(1)

    redis.ping.side_effect = hang

    response = await api_client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "fail"


async def test_health_probes_are_not_part_of_the_api_schema(api_client) -> None:
    response = await api_client.get("/api/openapi.json")

    assert "/livez" not in response.json()["paths"]
    assert "/readyz" not in response.json()["paths"]
