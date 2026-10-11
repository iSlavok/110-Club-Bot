from dishka import FromDishka
from loguru import logger

from app.telegram import RateLimitMiddleware


async def cleanup_rate_limiters(rate_limit: FromDishka[RateLimitMiddleware]) -> None:
    removed = rate_limit.cleanup_expired()
    logger.debug("Dropped {} idle chat rate limiters", removed)
