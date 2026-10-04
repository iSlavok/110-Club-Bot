from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from api import health
from api.core.errors import register_error_handlers


def create_app(container: AsyncContainer) -> FastAPI:
    app = FastAPI(title="110 Club Admin API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    register_error_handlers(app)
    app.include_router(health.router)
    setup_dishka(container, app)
    return app
