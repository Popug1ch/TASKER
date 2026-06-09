"""
Модуль маршрутов для работы с событиями (events).
События не имеют времени, только дату.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from core.database import SessionDep
from models.events import EventModel
from schemas.event import Event, EventAdd, EventUpdate
from repository.event_repository import EventRepository
from core.dependencies import get_current_user
from models.user import UserModel
from datetime import date

router = APIRouter(prefix="/api/events", tags=["События"])


@router.get("/all")
async def get_all_events(
    session: SessionDep, current_user: UserModel = Depends(get_current_user)
) -> list[Event]:
    """
    Возвращает все события текущего пользователя.

    Параметры:
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        list[Event]: список событий.
    """
    return await EventRepository.find_all(session, current_user.id)


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventAdd,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> Event:
    """
    Создаёт новое событие.

    Параметры:
        event (EventAdd): данные события (название, дата).
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        Event: созданное событие.

    Исключения:
        400: на выбранную дату уже есть 3 события.
    """
    count = await EventRepository.count_by_date(
        session, event.event_date, current_user.id
    )
    if count >= 3:
        raise HTTPException(400, "В этот день уже есть 3 события")
    return await EventRepository.add_one(event, session, current_user.id)


@router.get("/{event_date}")
async def get_events_by_date(
    event_date: date,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> list[Event]:
    """
    Возвращает события на конкретную дату.

    Параметры:
        event_date (date): дата.
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        list[Event]: список событий.
    """
    return await EventRepository.find_by_date(session, event_date, current_user.id)


@router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> Event:
    """
    Обновляет событие.

    Параметры:
        event_id (int): ID события.
        event_data (EventUpdate): новые данные.
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        Event: обновлённое событие.

    Исключения:
        404: событие не найдено.
        400: при смене даты превышен лимит (3 события на новую дату).
    """
    if event_data.event_date:
        count = await EventRepository.count_by_date(
            session, event_data.event_date, current_user.id
        )
        old_event = await session.get(EventModel, event_id)
        if (
            old_event
            and old_event.user_id == current_user.id
            and old_event.event_date != event_data.event_date
        ):
            if count >= 3:
                raise HTTPException(400, "В этот день уже есть 3 события")
    updated = await EventRepository.update_event(
        event_id, event_data, session, current_user.id
    )
    if not updated:
        raise HTTPException(404, "Событие не найдено")
    return updated


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """
    Удаление события.

    Параметры:
        event_id (int): ID события.
        session (SessionDep): сессия БД.
        current_user (UserModel): текущий пользователь.

    Возвращает:
        dict: сообщение об успехе.

    Исключения:
        404: событие не найдено.
    """
    deleted = await EventRepository.delete_event(event_id, session, current_user.id)
    if not deleted:
        raise HTTPException(404, "Событие не найдено")
    return {"success": True}
