from fastapi import APIRouter, HTTPException, status
from database import SessionDep
from models.deadline import DeadlineModel
from schemas.deadline import Deadline, DeadlineAdd, DeadlineUpdate
from repository import DeadlineRepository
from datetime import datetime

router = APIRouter()


@router.get("/all")
async def get_all_deadlines(session: SessionDep):
    deadlines = await DeadlineRepository.find_all(session)
    return deadlines


@router.post("", response_model=Deadline, status_code=status.HTTP_201_CREATED)
async def create_deadline(deadline: DeadlineAdd, session: SessionDep):
    # Проверка на максимум 3 дедлайнов в день
    count = await DeadlineRepository.count_by_date(session, deadline.deadline_time)
    if count >= 3:
        raise HTTPException(400, "В этот день уже есть 3 дедлайна")
    return await DeadlineRepository.add_one(deadline, session)


@router.get("/{deadline_time}")
async def get_deadlines_by_date(deadline_time: datetime, session: SessionDep):
    deadlines = await DeadlineRepository.find_by_date(session, deadline_time)
    return deadlines


@router.put("/{deadline_id}", response_model=Deadline)
async def update_deadline(deadline_id: int, deadline_data: DeadlineUpdate, session: SessionDep):
    # При смене даты нужно перепроверить лимит
    if deadline_data.deadline_time:
        count = await DeadlineRepository.count_by_date(session, deadline_data.deadline_time)
        # если событие перемещается на другой день, и там уже 3, то запретить
        # но сначала получим старое событие, чтобы не считать его же
        old_deadline = await session.get(DeadlineModel, deadline_id)
        if old_deadline and old_deadline.deadline_time != deadline_data.deadline_time:
            if count >= 3:
                raise HTTPException(400, "В этот день уже есть 3 дедлайна")
    updated = await DeadlineRepository.update_deadline(deadline_id, deadline_data, session)
    if not updated:
        raise HTTPException(404, "Дедлайн не найден")
    return updated


@router.delete("/{deadline_id}")
async def delete_deadline(deadline_id: int, session: SessionDep):
    deleted = await DeadlineRepository.delete_deadline(deadline_id, session)
    if not deleted:
        raise HTTPException(404, "Дедлайн не найден")
    return {"success": True}
