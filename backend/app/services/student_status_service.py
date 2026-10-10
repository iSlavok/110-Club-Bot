from app.exceptions import UserNotRegisteredError
from app.repositories import UserRepository
from app.schemas import StudentStatus
from app.services.chat_access_service import ChatAccessService


class StudentStatusService:
    def __init__(self, *, user_repository: UserRepository, chat_access_service: ChatAccessService) -> None:
        self._user_repository = user_repository
        self._chat_access_service = chat_access_service

    async def build(self, tg_id: int) -> StudentStatus:
        user = await self._user_repository.get_by_tg_id(tg_id)
        if user is None:
            raise UserNotRegisteredError
        clubs = await self._chat_access_service.student_clubs(user.id)
        return StudentStatus(vk_id=user.vk_id, clubs=clubs)
