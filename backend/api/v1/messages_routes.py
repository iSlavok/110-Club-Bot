from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, status

from api.core.auth import require
from api.core.params import IdPath
from api.core.routing import UnitOfWorkRoute
from api.schemas.reminder_schemas import ReminderResponse
from app.enums import Permission
from app.schemas import ClubMessageCreate, ClubMessageUpdate
from app.services import ClubMessageService

router = APIRouter(tags=["messages"], route_class=UnitOfWorkRoute)


@router.post(
    "/clubs/{club_id}/messages",
    dependencies=[require(Permission.MESSAGES_SEND)],
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    club_id: IdPath,
    body: ClubMessageCreate,
    club_message_service: FromDishka[ClubMessageService],
) -> ReminderResponse:
    message = await club_message_service.create(club_id, body)
    return ReminderResponse.from_dto(message)


@router.patch("/messages/{message_id}", dependencies=[require(Permission.MESSAGES_SEND)])
async def update_message(
    message_id: IdPath,
    patch: ClubMessageUpdate,
    club_message_service: FromDishka[ClubMessageService],
) -> ReminderResponse:
    message = await club_message_service.update(message_id, patch)
    return ReminderResponse.from_dto(message)


@router.post("/messages/{message_id}/cancel", dependencies=[require(Permission.MESSAGES_SEND)])
async def cancel_message(
    message_id: IdPath,
    club_message_service: FromDishka[ClubMessageService],
) -> ReminderResponse:
    message = await club_message_service.cancel(message_id)
    return ReminderResponse.from_dto(message)
