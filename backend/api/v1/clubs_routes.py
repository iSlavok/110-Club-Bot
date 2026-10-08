from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Query, status

from api.core.auth import require
from api.core.params import IdPath
from api.core.routing import UnitOfWorkRoute
from api.schemas import Page
from api.schemas.club_schemas import BlockResponse, ClubResponse
from app.enums import Permission
from app.schemas import BlockCreate, BlockUpdate, ClubCreate, ClubUpdate, PageParams
from app.services import BlockService, ClubService

router = APIRouter(tags=["clubs"], route_class=UnitOfWorkRoute)


@router.get("/clubs", dependencies=[require(Permission.CLUBS_VIEW)])
async def list_clubs(
    page: Annotated[PageParams, Query()],
    club_service: FromDishka[ClubService],
) -> Page[ClubResponse]:
    clubs = await club_service.list_page(page)
    return Page.from_paginated(clubs, page, ClubResponse.from_dto)


@router.post("/clubs", dependencies=[require(Permission.CLUBS_EDIT)], status_code=status.HTTP_201_CREATED)
async def create_club(body: ClubCreate, club_service: FromDishka[ClubService]) -> ClubResponse:
    club = await club_service.create(body)
    return ClubResponse.from_dto(club)


@router.get("/clubs/{club_id}", dependencies=[require(Permission.CLUBS_VIEW)])
async def get_club(club_id: IdPath, club_service: FromDishka[ClubService]) -> ClubResponse:
    club = await club_service.get(club_id)
    return ClubResponse.from_dto(club)


@router.patch("/clubs/{club_id}", dependencies=[require(Permission.CLUBS_EDIT)])
async def update_club(club_id: IdPath, patch: ClubUpdate, club_service: FromDishka[ClubService]) -> ClubResponse:
    club = await club_service.update(club_id, patch)
    return ClubResponse.from_dto(club)


@router.get("/clubs/{club_id}/blocks", dependencies=[require(Permission.CLUBS_VIEW)])
async def list_blocks(
    club_id: IdPath,
    page: Annotated[PageParams, Query()],
    block_service: FromDishka[BlockService],
) -> Page[BlockResponse]:
    blocks = await block_service.list_page(club_id, page)
    return Page.from_paginated(blocks, page, BlockResponse.from_dto)


@router.post(
    "/clubs/{club_id}/blocks", dependencies=[require(Permission.BLOCKS_EDIT)], status_code=status.HTTP_201_CREATED
)
async def create_block(club_id: IdPath, body: BlockCreate, block_service: FromDishka[BlockService]) -> BlockResponse:
    block = await block_service.create(club_id, body)
    return BlockResponse.from_dto(block)


@router.patch("/blocks/{block_id}", dependencies=[require(Permission.BLOCKS_EDIT)])
async def update_block(block_id: IdPath, patch: BlockUpdate, block_service: FromDishka[BlockService]) -> BlockResponse:
    block = await block_service.update(block_id, patch)
    return BlockResponse.from_dto(block)


@router.delete(
    "/blocks/{block_id}", dependencies=[require(Permission.BLOCKS_EDIT)], status_code=status.HTTP_204_NO_CONTENT
)
async def delete_block(block_id: IdPath, block_service: FromDishka[BlockService]) -> None:
    await block_service.delete(block_id)
