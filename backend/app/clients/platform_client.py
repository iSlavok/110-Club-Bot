from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from loguru import logger

from app.clients.exceptions import PlatformNotConfiguredError
from app.config import PlatformSettings
from app.schemas import PlatformCourse, PlatformLesson

_CLIENT_PACKAGE = "points_api"


class PlatformClient(Protocol):
    async def get_course(self, course_id: int) -> PlatformCourse: ...

    async def get_lesson(self, lesson_id: int) -> PlatformLesson: ...


class DisabledPlatformClient:
    async def get_course(self, course_id: int) -> PlatformCourse:  # noqa: ARG002 - PlatformClient signature
        raise PlatformNotConfiguredError

    async def get_lesson(self, lesson_id: int) -> PlatformLesson:  # noqa: ARG002 - PlatformClient signature
        raise PlatformNotConfiguredError


# The client of the platform API is a private package: a build without it runs with the integration off.
@asynccontextmanager
async def open_platform_client(settings: PlatformSettings) -> AsyncIterator[PlatformClient]:
    if settings.token is None:
        logger.warning("PLATFORM_TOKEN is not set, linking lessons to the platform is unavailable")
        yield DisabledPlatformClient()
        return
    try:
        from app.clients.points_platform_client import open_points_platform_client  # noqa: PLC0415 - optional package
    except ModuleNotFoundError as error:
        if error.name != _CLIENT_PACKAGE:
            raise
        logger.warning("The {} package is not installed, linking lessons to the platform is unavailable", error.name)
        yield DisabledPlatformClient()
        return
    async with open_points_platform_client(settings.token.get_secret_value()) as client:
        yield client
