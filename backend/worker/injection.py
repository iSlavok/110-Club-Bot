from collections.abc import Awaitable, Callable

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection


# Jobs take only FromDishka parameters, so the wrapper APScheduler calls has no arguments of its own.
def inject_job(container: AsyncContainer, job: Callable[..., Awaitable[None]]) -> Callable[[], Awaitable[None]]:
    return wrap_injection(
        func=job,
        container_getter=lambda _args, _kwargs: container,
        is_async=True,
        manage_scope=True,
    )
