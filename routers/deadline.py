from fastapi import APIRouter, HTTPException, status, Depends
from database import SessionDep
from models.deadline import DeadlineModel
from schemas.deadline import Deadline, DeadlineAdd, DeadlineUpdate
from repository import DeadlineRepository
from dependencies import get_current_user
from models.user import UserModel
from datetime import datetime

router = APIRouter(prefix="/api/deadlines", tags=["Дедлайны"])


@router.get("/all")
async def get_all_deadlines(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    return await DeadlineRepository.find_all(session, current_user.id)


@router.get("/active")
async def get_active_deadlines(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    return await DeadlineRepository.find_active(session, current_user.id)


@router.post("", response_model=Deadline, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    deadline: DeadlineAdd,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    count_on_day = await DeadlineRepository.count_by_date(session, deadline.deadline_time, current_user.id)
    if count_on_day >= 3:
        raise HTTPException(400, "В этот день уже есть 3 дедлайна")
    active_count = await DeadlineRepository.count_active(session, current_user.id)
    if active_count >= 9:
        raise HTTPException(400, "Слишком много активных дедлайнов (максимум 9)")
    return await DeadlineRepository.add_one(deadline, session, current_user.id)


@router.get("/{deadline_date}")
async def get_deadlines_by_date(
    deadline_date: datetime,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    return await DeadlineRepository.find_by_date(session, deadline_date, current_user.id)


@router.put("/{deadline_id}", response_model=Deadline)
async def update_deadline(
    deadline_id: int,
    deadline_data: DeadlineUpdate,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    old_deadline = await session.get(DeadlineModel, deadline_id)
    if not old_deadline or old_deadline.user_id != current_user.id:
        raise HTTPException(404, "Дедлайн не найден")
    if deadline_data.deadline_time and old_deadline.deadline_time.date() != deadline_data.deadline_time.date():
        count = await DeadlineRepository.count_by_date(session, deadline_data.deadline_time, current_user.id)
        if count >= 3:
            raise HTTPException(400, "На новую дату уже есть 3 дедлайна")
    updated = await DeadlineRepository.update_deadline(deadline_id, deadline_data, session, current_user.id)
    if not updated:
        raise HTTPException(404, "Дедлайн не найден")
    return updated


@router.put("/{deadline_id}/status")
async def update_deadline_status(
    deadline_id: int,
    is_completed: bool,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    updated = await DeadlineRepository.update_status(deadline_id, is_completed, session, current_user.id)
    if not updated:
        raise HTTPException(404, "Дедлайн не найден")
    return {"success": True}


@router.delete("/{deadline_id}")
async def delete_deadline(
    deadline_id: int,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    deleted = await DeadlineRepository.delete_deadline(deadline_id, session, current_user.id)
    if not deleted:
        raise HTTPException(404, "Дедлайн не найден")
    return {"success": True}