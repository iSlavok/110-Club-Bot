from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from api.core.routing import UnitOfWorkRoute
from api.schemas.vk_schemas import VkCallbackParams
from app import texts
from app.services import VkLinkService

router = APIRouter(prefix="/vk", tags=["vk"], route_class=UnitOfWorkRoute, include_in_schema=False)


def _page(title: str, text: str) -> str:
    return (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{title}</title></head>"
        '<body style="font-family: system-ui, sans-serif; max-width: 32rem; margin: 3rem auto; padding: 0 1rem">'
        f"<h1>{title}</h1><p>{text}</p></body></html>"
    )


EXPIRED_PAGE = _page(texts.vk_link.CALLBACK_EXPIRED_TITLE, texts.vk_link.CALLBACK_EXPIRED_TEXT)
DONE_PAGE = _page(texts.vk_link.CALLBACK_DONE_TITLE, texts.vk_link.CALLBACK_DONE_TEXT)


# VK ID redirects the student's browser here (see VK_CALLBACK_PATH); the result goes to them in Telegram.
@router.get("/callback")
async def vk_callback(
    params: Annotated[VkCallbackParams, Query()],
    vk_link_service: FromDishka[VkLinkService],
) -> Response:
    completion = await vk_link_service.complete_oauth(
        state=params.state,
        code=params.code,
        device_id=params.device_id,
        error=params.error,
    )
    if completion.is_expired:
        return HTMLResponse(EXPIRED_PAGE, status_code=status.HTTP_400_BAD_REQUEST)
    if completion.bot_username is None:
        return HTMLResponse(DONE_PAGE)
    return RedirectResponse(f"https://t.me/{completion.bot_username}", status_code=status.HTTP_302_FOUND)
