from dishka import FromDishka

from app.services import AuthCleanupService


async def purge_expired_auth(auth_cleanup_service: FromDishka[AuthCleanupService]) -> None:
    await auth_cleanup_service.purge_expired()
