from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from api.core.auth import require
from api.schemas import Page
from api.schemas.users import UserListParams, UserResponse
from app.enums import Permission
from app.services import UserService

router = APIRouter(prefix="/users", tags=["users"], route_class=DishkaRoute)


@router.get("", dependencies=[require(Permission.USERS_VIEW)])
async def list_users(
    params: Annotated[UserListParams, Query()],
    user_service: FromDishka[UserService],
) -> Page[UserResponse]:
    users = await user_service.search_page(params.q, params)
    return Page.from_paginated(users, params, UserResponse.from_dto)
