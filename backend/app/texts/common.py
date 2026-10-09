from app.schemas import UserDTO

UNEXPECTED_ERROR = "Что-то пошло не так. Попробуй ещё раз чуть позже."


def greeting(user: UserDTO) -> str:
    return f"Привет, {user.full_name}! Это бот клуба 110."
