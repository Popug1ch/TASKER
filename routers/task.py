from typing import Optional
from datetime import datetime, time
from fastapi import APIRouter, HTTPException, status, Query
from database import SessionDep
from schemas.task import STask, STaskAdd, STaskUpdate
from repository import TaskRepository

router = APIRouter(prefix="/api/tasks", tags=["Задачи"])


@router.post("", response_model=STask, status_code=status.HTTP_201_CREATED)
async def create_task(task: STaskAdd, session: SessionDep):
    return await TaskRepository.add_one(task, session)


@router.get("", response_model=list[STask])
async def get_tasks(
    session: SessionDep,
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
):
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Неверный формат даты, используйте YYYY-MM-DD"
            )
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)
        tasks = await TaskRepository.find_in_range(session, start_of_day, end_of_day)
    else:
        tasks = await TaskRepository.find_all(session)
    return tasks


@router.put("/{task_id}/status")
async def update_task_status(task_id: int, is_completed: bool, session: SessionDep):
    updated = await TaskRepository.update_status(task_id, is_completed, session)
    if updated is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"success": True}


@router.put("/{task_id}", response_model=STask)
async def update_task(task_id: int, task_data: STaskUpdate, session: SessionDep):
    updated = await TaskRepository.update_task(task_id, task_data, session)
    if updated is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return updated


@router.delete("/{task_id}")
async def delete_task(task_id: int, session: SessionDep):
    deleted = await TaskRepository.delete_task(task_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"success": True}
