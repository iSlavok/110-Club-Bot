from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Query

from api.core.auth import require
from api.core.params import IdPath
from api.core.routing import UnitOfWorkRoute
from api.schemas import Page
from api.schemas.sheet_sync_schemas import SheetSyncResponse
from app.enums import Permission
from app.schemas import PageParams
from app.services import SheetSyncService

router = APIRouter(tags=["sync"], route_class=UnitOfWorkRoute)


# Runs inside the request: api and worker share one process, so no queue is needed for "sync now".
@router.post("/clubs/{club_id}/sync", dependencies=[require(Permission.SYNC_RUN)])
async def sync_club(club_id: IdPath, sheet_sync_service: FromDishka[SheetSyncService]) -> SheetSyncResponse:
    sync = await sheet_sync_service.sync_club(club_id)
    return SheetSyncResponse.from_dto(sync)


@router.get("/clubs/{club_id}/syncs", dependencies=[require(Permission.CLUBS_VIEW)])
async def list_club_syncs(
    club_id: IdPath,
    page: Annotated[PageParams, Query()],
    sheet_sync_service: FromDishka[SheetSyncService],
) -> Page[SheetSyncResponse]:
    syncs = await sheet_sync_service.list_page(club_id, page)
    return Page.from_paginated(syncs, page, SheetSyncResponse.from_dto)
