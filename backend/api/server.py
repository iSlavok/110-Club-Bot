import contextlib
from collections.abc import Iterator

import uvicorn
from fastapi import FastAPI

from app.config import ApiSettings


class _Server(uvicorn.Server):
    # Shutdown signals are owned by main.py: uvicorn's handler would re-raise SIGTERM and kill the bot mid-update.
    @contextlib.contextmanager
    def capture_signals(self) -> Iterator[None]:
        yield


def create_server(app: FastAPI, settings: ApiSettings) -> uvicorn.Server:
    config = uvicorn.Config(
        app, host=settings.host, port=settings.port, log_config=None, access_log=False, lifespan="off"
    )
    return _Server(config)
