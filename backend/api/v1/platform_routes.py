from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter

from api.core.auth import require
from api.core.params import IdPath
from api.core.routing import UnitOfWorkRoute
from api.schemas.platform_schemas import PlatformCourseResponse, PlatformLessonResponse
from app.enums import Permission
from app.services import PlatformService

router = APIRouter(tags=["platform"], route_class=UnitOfWorkRoute)


@router.get("/clubs/{club_id}/platform-course", dependencies=[require(Permission.LESSONS_EDIT)])
async def get_club_platform_course(
    club_id: IdPath,
    platform_service: FromDishka[PlatformService],
) -> PlatformCourseResponse:
    course = await platform_service.course_outline(club_id)
    return PlatformCourseResponse.from_dto(course)


@router.get("/platform/lessons/{platform_lesson_id}", dependencies=[require(Permission.LESSONS_EDIT)])
async def get_platform_lesson(
    platform_lesson_id: IdPath,
    platform_service: FromDishka[PlatformService],
) -> PlatformLessonResponse:
    lesson = await platform_service.lesson(platform_lesson_id)
    return PlatformLessonResponse.from_dto(lesson)
