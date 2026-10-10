from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Query

from api.core.auth import require
from api.core.params import IdPath
from api.core.routing import UnitOfWorkRoute
from api.schemas import Page
from api.schemas.reminder_schemas import ReminderListParams, ReminderPreviewResponse, ReminderResponse
from app.enums import Permission
from app.services import ReminderService

router = APIRouter(tags=["reminders"], route_class=UnitOfWorkRoute)


@router.get("/clubs/{club_id}/reminders", dependencies=[require(Permission.LESSONS_VIEW)])
async def list_reminders(
    club_id: IdPath,
    params: Annotated[ReminderListParams, Query()],
    reminder_service: FromDishka[ReminderService],
) -> Page[ReminderResponse]:
    reminders = await reminder_service.list_page(
        club_id,
        params,
        view=params.view,
        include_cancelled=params.include_cancelled,
        lesson_id=params.lesson_id,
    )
    return Page.from_paginated(reminders, params, ReminderResponse.from_dto)


@router.get("/reminders/{reminder_id}/preview", dependencies=[require(Permission.LESSONS_VIEW)])
async def preview_reminder(
    reminder_id: IdPath,
    reminder_service: FromDishka[ReminderService],
) -> ReminderPreviewResponse:
    html = await reminder_service.preview(reminder_id)
    return ReminderPreviewResponse(html=html)


@router.post("/reminders/{reminder_id}/cancel", dependencies=[require(Permission.LESSONS_EDIT)])
async def cancel_reminder(reminder_id: IdPath, reminder_service: FromDishka[ReminderService]) -> ReminderResponse:
    reminder = await reminder_service.cancel(reminder_id)
    return ReminderResponse.from_dto(reminder)
