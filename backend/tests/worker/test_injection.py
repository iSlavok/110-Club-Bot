from dishka import AsyncContainer, FromDishka

from app.services import UserService
from worker import inject_job


async def test_inject_job_resolves_dependencies_in_a_fresh_scope_per_run(container: AsyncContainer) -> None:
    received: list[UserService] = []

    async def job(user_service: FromDishka[UserService]) -> None:
        received.append(user_service)

    injected = inject_job(container, job)
    await injected()
    await injected()

    assert len(received) == 2
    assert all(isinstance(service, UserService) for service in received)
    assert received[0] is not received[1]
