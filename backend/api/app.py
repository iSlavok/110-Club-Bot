from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from api import health_routes
from api.core.errors import register_error_handlers
from api.v1 import create_v1_router


def create_app(container: AsyncContainer) -> FastAPI:
    app = FastAPI(title="110 Club Admin API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    register_error_handlers(app)
    app.include_router(health_routes.router)
    app.include_router(create_v1_router())
    setup_dishka(container, app)
    return app
