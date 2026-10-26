from app.exceptions import UserNotRegisteredError
from app.models import Lesson
from app.repositories import LessonRepository, UserRepository
from app.schemas import ClubSchedule, ScheduleItem
from app.services.chat_access_service import ChatAccessService
from app.utils import Clock


# A student sees the schedule of the clubs they have access to (an admin: of every club), up to the end of that block.
class ScheduleService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        lesson_repository: LessonRepository,
        chat_access_service: ChatAccessService,
        clock: Clock,
    ) -> None:
        self._user_repository = user_repository
        self._lesson_repository = lesson_repository
        self._chat_access_service = chat_access_service
        self._clock = clock

    async def build(self, tg_id: int) -> list[ClubSchedule]:
        user = await self._user_repository.get_by_tg_id(tg_id)
        if user is None:
            raise UserNotRegisteredError
        now = self._clock.now()
        schedules: list[ClubSchedule] = []
        club_blocks = await self._chat_access_service.access_blocks(user)
        for club, block in club_blocks:
            lessons = await self._lesson_repository.list_for_schedule(club_id=club.id, start=now, end=block.ends_at)
            items = [item for lesson in lessons for item in _items(lesson)]
            items = [item for item in items if now <= item.moment < block.ends_at]
            items.sort(key=lambda item: item.moment)
            schedules.append(ClubSchedule(club_title=club.title, block_title=block.title, items=items))
        return schedules


def _items(lesson: Lesson) -> list[ScheduleItem]:
    items = [
        ScheduleItem(
            moment=lesson.starts_at,
            lesson_kind=lesson.kind,
            lesson_title=lesson.title,
            is_homework_deadline=False,
        ),
    ]
    if lesson.homework_deadline_at is not None:
        items.append(
            ScheduleItem(
                moment=lesson.homework_deadline_at,
                lesson_kind=lesson.kind,
                lesson_title=lesson.title,
                is_homework_deadline=True,
            ),
        )
    return items
