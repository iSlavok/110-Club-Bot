import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api import create_app
from app.exceptions import AppError, NotFoundError


class WidgetNotFoundError(NotFoundError):
    pass


def _raise(error: Exception) -> None:
    raise error


def _echo(n: int) -> int:
    return n


@pytest.fixture
def app(container: AsyncContainer) -> FastAPI:
    app = create_app(container)
    app.add_api_route("/boom/not-found", lambda: _raise(WidgetNotFoundError("widget 1 not found")))
    app.add_api_route("/boom/untagged", lambda: _raise(AppError("weird")))
    app.add_api_route("/boom/crash", lambda: _raise(RuntimeError("secret details")))
    app.add_api_route("/boom/validated", _echo)
    return app


@pytest.fixture
async def client(app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as c:
        yield c


async def test_tagged_error_maps_to_status_and_code(client) -> None:
    response = await client.get("/boom/not-found")

    assert response.status_code == 404
    assert response.json() == {"code": "WIDGET_NOT_FOUND", "message": "widget 1 not found"}


async def test_untagged_app_error_is_500(client) -> None:
    response = await client.get("/boom/untagged")

    assert response.status_code == 500
    assert response.json()["code"] == "APP"


async def test_unexpected_error_hides_details(client) -> None:
    response = await client.get("/boom/crash")

    assert response.status_code == 500
    assert response.json() == {"code": "INTERNAL_ERROR", "message": "Internal server error"}


async def test_request_validation_uses_common_contract(client) -> None:
    response = await client.get("/boom/validated", params={"n": "not-a-number"})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"
