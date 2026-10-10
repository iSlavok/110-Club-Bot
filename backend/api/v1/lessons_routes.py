from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Query, status

from api.core.auth import require
from api.core.params import IdPath
from api.core.routing import UnitOfWorkRoute
from api.schemas import Page
from api.schemas.lesson_schemas import LessonCancelRequest, LessonListParams, LessonResponse
from app.enums import Permission
from app.schemas import LessonCreate, LessonUpdate
from app.services import LessonService

router = APIRouter(tags=["lessons"], route_class=UnitOfWorkRoute)


@router.get("/clubs/{club_id}/lessons", dependencies=[require(Permission.LESSONS_VIEW)])
async def list_lessons(
    club_id: IdPath,
    params: Annotated[LessonListParams, Query()],
    lesson_service: FromDishka[LessonService],
) -> Page[LessonResponse]:
    lessons = await lesson_service.list_page(
        club_id,
        params,
        view=params.view,
        include_cancelled=params.include_cancelled,
    )
    return Page.from_paginated(lessons, params, LessonResponse.from_dto)


@router.post(
    "/clubs/{club_id}/lessons",
    dependencies=[require(Permission.LESSONS_EDIT)],
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson(
    club_id: IdPath, body: LessonCreate, lesson_service: FromDishka[LessonService]
) -> LessonResponse:
    lesson = await lesson_service.create(club_id, body)
    return LessonResponse.from_dto(lesson)


@router.get("/lessons/{lesson_id}", dependencies=[require(Permission.LESSONS_VIEW)])
async def get_lesson(lesson_id: IdPath, lesson_service: FromDishka[LessonService]) -> LessonResponse:
    lesson = await lesson_service.get(lesson_id)
    return LessonResponse.from_dto(lesson)


@router.patch("/lessons/{lesson_id}", dependencies=[require(Permission.LESSONS_EDIT)])
async def update_lesson(
    lesson_id: IdPath,
    patch: LessonUpdate,
    lesson_service: FromDishka[LessonService],
    *,
    notify_chat: Annotated[
        bool,
        Query(description="Tell the club chat about a new start time, a moved deadline or removed homework"),
    ] = False,
) -> LessonResponse:
    lesson = await lesson_service.update(lesson_id, patch, notify_chat=notify_chat)
    return LessonResponse.from_dto(lesson)


@router.post("/lessons/{lesson_id}/cancel", dependencies=[require(Permission.LESSONS_EDIT)])
async def cancel_lesson(
    lesson_id: IdPath,
    body: LessonCancelRequest,
    lesson_service: FromDishka[LessonService],
) -> LessonResponse:
    lesson = await lesson_service.cancel(lesson_id, notify_chat=body.notify_chat)
    return LessonResponse.from_dto(lesson)
