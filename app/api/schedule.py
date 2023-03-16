from fastapi import (
    APIRouter,
    Depends,
)
from starlette.responses import JSONResponse

from app.services.schedule import ScheduleService

router = APIRouter(
    prefix='/schedule',
    tags=['schedule'],
)


@router.get("/group/{group_id}")
async def get_schedule_group(group_id: int):
    pass