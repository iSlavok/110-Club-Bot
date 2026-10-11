from collections.abc import Callable, Coroutine
from typing import Any

from dishka import AsyncContainer
from dishka.integrations.fastapi import DishkaRoute
from fastapi import FastAPI, Request, Response


def attach_container(app: FastAPI, container: AsyncContainer) -> None:
    app.state.dishka_container = container


# The request scope (and so the transaction) wraps only the endpoint, not the whole ASGI app as dishka's middleware
# does: domain errors reach DatabaseProvider before the exception handlers turn them into responses, and the commit
# happens before the response is sent, so a failed commit is still a 500.
class UnitOfWorkRoute(DishkaRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            app_container: AsyncContainer = request.app.state.dishka_container
            async with app_container({Request: request}) as request_container:
                request.state.dishka_container = request_container
                return await handler(request)

        return handle
