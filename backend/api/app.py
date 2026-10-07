from dishka import AsyncContainer
from fastapi import FastAPI
from fastapi.routing import APIRoute

from api import health_routes
from api.core.errors import register_error_handlers
from api.core.routing import attach_container
from api.v1 import create_v1_router


# operationId becomes the generated frontend hook name: list_clubs -> useListClubs. Route names must stay unique.
def _operation_id(route: APIRoute) -> str:
    return route.name


def create_app(container: AsyncContainer) -> FastAPI:
    app = FastAPI(
        title="110 Club Admin API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        generate_unique_id_function=_operation_id,
    )
    register_error_handlers(app)
    app.include_router(health_routes.router)
    app.include_router(create_v1_router())
    attach_container(app, container)
    return app
