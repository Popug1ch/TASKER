from fastapi import APIRouter, HTTPException, status
from database import SessionDep
from models.deadline import DeadlineModel
from schemas.deadline import Deadline, DeadlineAdd, DeadlineUpdate
from repository import DeadlineRepository
from datetime import datetime

router = APIRouter(prefix="/api/deadlines", tags=["Дедлайны"])

@router.get("/all")
async def get_all_deadlines(session: SessionDep):
    deadlines = await DeadlineRepository.find_all(session)
    return deadlines

@router.get("/active")
async def get_active_deadlines(session: SessionDep):
    deadlines = await DeadlineRepository.find_active(session)
    return deadlines

@router.post("", response_model=Deadline, status_code=status.HTTP_201_CREATED)
async def create_deadline(deadline: DeadlineAdd, session: SessionDep):
    # Проверка на максимум 3 дедлайна в указанный день
    count_on_day = await DeadlineRepository.count_by_date(session, deadline.deadline_time)
    if count_on_day >= 3:
        raise HTTPException(400, "В этот день уже есть 3 дедлайна")
    # Проверка на максимум 9 активных дедлайнов (невыполненных)
    active_count = await DeadlineRepository.count_active(session)
    if active_count >= 9:
        raise HTTPException(400, "Слишком много активных дедлайнов (максимум 9). Завершите часть.")
    return await DeadlineRepository.add_one(deadline, session)

@router.get("/{deadline_date}")
async def get_deadlines_by_date(deadline_date: datetime, session: SessionDep):
    deadlines = await DeadlineRepository.find_by_date(session, deadline_date)
    return deadlines

@router.put("/{deadline_id}", response_model=Deadline)
async def update_deadline(deadline_id: int, deadline_data: DeadlineUpdate, session: SessionDep):
    # При смене даты перепроверяем лимит на день
    old_deadline = await session.get(DeadlineModel, deadline_id)
    if not old_deadline:
        raise HTTPException(404, "Дедлайн не найден")
    if deadline_data.deadline_time and old_deadline.deadline_time.date() != deadline_data.deadline_time.date():
        count = await DeadlineRepository.count_by_date(session, deadline_data.deadline_time)
        if count >= 3:
            raise HTTPException(400, "На новую дату уже есть 3 дедлайна")
    # Если меняется статус на выполнено – активных станет меньше, проверка не нужна
    updated = await DeadlineRepository.update_deadline(deadline_id, deadline_data, session)
    if not updated:
        raise HTTPException(404, "Дедлайн не найден")
    return updated

@router.put("/{deadline_id}/status")
async def update_deadline_status(deadline_id: int, is_completed: bool, session: SessionDep):
    updated = await DeadlineRepository.update_status(deadline_id, is_completed, session)
    if not updated:
        raise HTTPException(404, "Дедлайн не найден")
    return {"success": True}

@router.delete("/{deadline_id}")
async def delete_deadline(deadline_id: int, session: SessionDep):
    deleted = await DeadlineRepository.delete_deadline(deadline_id, session)
    if not deleted:
        raise HTTPException(404, "Дедлайн не найден")
    return {"success": True}