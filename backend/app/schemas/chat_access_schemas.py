from pydantic import BaseModel


class ChatStudent(BaseModel):
    vk_id: int
    full_name: str
    tg_username: str | None
