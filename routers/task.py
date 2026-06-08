from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from database import SessionDep
from schemas.task import STask, STaskAdd, STaskUpdate
from repository import TaskRepository
from dependencies import get_current_user
from models.user import UserModel

router = APIRouter(prefix="/api/tasks", tags=["Задачи"])


@router.post("", response_model=STask, status_code=201)
async def create_task(
    task: STaskAdd,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    return await TaskRepository.add_one(task, session, current_user.id)


@router.get("", response_model=list[STask])
async def get_tasks(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date) + timedelta(days=1)
        except ValueError:
            raise HTTPException(400, "Неверный формат даты")
        tasks = await TaskRepository.find_in_range(session, start, end, current_user.id)
    else:
        tasks = await TaskRepository.find_all(session, current_user.id)
    return tasks


@router.get("/week/current")
async def get_current_week(session: SessionDep):
    start = await TaskRepository.get_current_week_start(session)
    end = start + timedelta(days=7)
    return {"week_start": start.isoformat(), "week_end": end.isoformat()}


@router.post("/week/rollover")
async def rollover_week(session: SessionDep):
    await TaskRepository.rollover_week(session)
    return {"success": True}


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: int,
    is_completed: bool,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    updated = await TaskRepository.update_status(task_id, is_completed, session, current_user.id)
    if updated is None:
        raise HTTPException(404, "Задача не найдена")
    return {"success": True}


@router.put("/{task_id}", response_model=STask)
async def update_task(
    task_id: int,
    task_data: STaskUpdate,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    updated = await TaskRepository.update_task(task_id, task_data, session, current_user.id)
    if updated is None:
        raise HTTPException(404, "Задача не найдена")
    return updated


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    deleted = await TaskRepository.delete_task(task_id, session, current_user.id)
    if not deleted:
        raise HTTPException(404, "Задача не найдена")
    return {"success": True}