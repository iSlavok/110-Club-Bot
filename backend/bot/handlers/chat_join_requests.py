from aiogram import Router
from aiogram.types import ChatJoinRequest
from dishka.integrations.aiogram import FromDishka

from app.services import ChatAccessService

router = Router(name="chat_join_requests")


@router.chat_join_request()
async def join_request(request: ChatJoinRequest, chat_access_service: FromDishka[ChatAccessService]) -> None:
    invite_link = request.invite_link.invite_link if request.invite_link is not None else None
    await chat_access_service.handle_join_request(
        chat_id=request.chat.id,
        tg_id=request.from_user.id,
        invite_link=invite_link,
    )
