"""
Модуль маршрутов для работы с задачами (tasks).
Поддерживает создание, чтение, обновление, удаление, а также механизм переноса недель.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from core.database import SessionDep
from schemas.task import STask, STaskAdd, STaskUpdate
from repository.task_repository import TaskRepository
from core.dependencies import get_current_user
from models.user import UserModel

router = APIRouter(prefix="/api/tasks", tags=["Задачи"])


@router.post("", response_model=STask, status_code=201)
async def create_task(
    task: STaskAdd,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> STask:
    """
    Создаёт новую задачу.

    Параметры:
        task (STaskAdd): данные задачи (название, start_time, end_time, категория, приоритет).
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        STask: созданная задача с автоматически вычисленной длительностью и id.
    """
    return await TaskRepository.add_one(task, session, current_user.id)


@router.get("", response_model=list[STask])
async def get_tasks(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
    start_date: Optional[str] = Query(
        None, description="Начало диапазона (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(None, description="Конец диапазона (YYYY-MM-DD)"),
) -> list[STask]:
    """
    Возвращает задачи пользователя. Если указаны start_date и end_date, возвращает задачи за диапазон,
    иначе – все задачи пользователя (используется для цветных точек в календаре).

    Параметры:
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.
        start_date (str, optional): начало диапазона в формате YYYY-MM-DD.
        end_date (str, optional): конец диапазона (включительно, добавится +1 день).

    Возвращает:
        list[STask]: список задач.

    Исключения:
        400: неверный формат даты.
    """
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
async def get_current_week(session: SessionDep) -> dict:
    """
    Возвращает даты начала и конца текущей (активной) недели.
    Используется клиентом для отображения календаря.

    Параметры:
        session (SessionDep): сессия БД.

    Возвращает:
        dict: объект с полями week_start, week_end (ISO-формат).
    """
    start = await TaskRepository.get_current_week_start(session)
    end = start + timedelta(days=7)
    return {"week_start": start.isoformat(), "week_end": end.isoformat()}


@router.post("/week/rollover")
async def rollover_week(session: SessionDep) -> dict:
    """
    Принудительно выполняет перенос задач (сдвиг активной недели).
    Обычно вызывается автоматически при старте приложения, но может быть вызван вручную.

    Параметры:
        session (SessionDep): сессия БД.

    Возвращает:
        dict: сообщение об успехе.
    """
    await TaskRepository.rollover_week(session)
    return {"success": True}


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: int,
    is_completed: bool,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """
    Обновляет статус задачи (выполнена / не выполнена).

    Параметры:
        task_id (int): ID задачи.
        is_completed (bool): новое состояние.
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        dict: сообщение об успехе.

    Исключения:
        404: задача не найдена или принадлежит другому пользователю.
    """
    updated = await TaskRepository.update_status(
        task_id, is_completed, session, current_user.id
    )
    if updated is None:
        raise HTTPException(404, "Задача не найдена")
    return {"success": True}


@router.put("/{task_id}", response_model=STask)
async def update_task(
    task_id: int,
    task_data: STaskUpdate,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> STask:
    """
    Полное обновление задачи (название, время, категория, приоритет).

    Параметры:
        task_id (int): ID задачи.
        task_data (STaskUpdate): новые данные.
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        STask: обновлённая задача.

    Исключения:
        404: задача не найдена.
    """
    updated = await TaskRepository.update_task(
        task_id, task_data, session, current_user.id
    )
    if updated is None:
        raise HTTPException(404, "Задача не найдена")
    return updated


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """
    Удаление задачи.

    Параметры:
        task_id (int): ID задачи.
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        dict: сообщение об успехе.

    Исключения:
        404: задача не найдена.
    """
    deleted = await TaskRepository.delete_task(task_id, session, current_user.id)
    if not deleted:
        raise HTTPException(404, "Задача не найдена")
    return {"success": True}
