import contextlib
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from app import texts
from app.exceptions import AppError


class ErrorsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:  # noqa: ANN401 - aiogram middleware contract
        try:
            return await handler(event, data)
        except AppError as exc:
            logger.info("Domain error in bot handler: {} {}", exc.code, exc.message)
            await _reply(event, texts.errors.for_error(exc))
        except Exception:  # noqa: BLE001 - last line of defence: log and keep the update loop alive
            logger.exception("Unhandled error in bot handler")
            await _reply(event, texts.common.UNEXPECTED_ERROR)
        return None


async def _reply(event: TelegramObject, text: str) -> None:
    with contextlib.suppress(TelegramAPIError):
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
