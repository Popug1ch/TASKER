from fastapi import APIRouter, HTTPException, status, Depends
from database import SessionDep
from models.events import EventModel
from schemas.event import Event, EventAdd, EventUpdate
from repository import EventRepository
from dependencies import get_current_user
from models.user import UserModel
from datetime import date

router = APIRouter(prefix="/api/events", tags=["События"])


@router.get("/all")
async def get_all_events(
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    return await EventRepository.find_all(session, current_user.id)


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventAdd,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    count = await EventRepository.count_by_date(session, event.event_date, current_user.id)
    if count >= 3:
        raise HTTPException(400, "В этот день уже есть 3 события")
    return await EventRepository.add_one(event, session, current_user.id)


@router.get("/{event_date}")
async def get_events_by_date(
    event_date: date,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    return await EventRepository.find_by_date(session, event_date, current_user.id)


@router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    if event_data.event_date:
        count = await EventRepository.count_by_date(session, event_data.event_date, current_user.id)
        old_event = await session.get(EventModel, event_id)
        if old_event and old_event.user_id == current_user.id and old_event.event_date != event_data.event_date:
            if count >= 3:
                raise HTTPException(400, "В этот день уже есть 3 события")
    updated = await EventRepository.update_event(event_id, event_data, session, current_user.id)
    if not updated:
        raise HTTPException(404, "Событие не найдено")
    return updated


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    session: SessionDep,
    current_user: UserModel = Depends(get_current_user)
):
    deleted = await EventRepository.delete_event(event_id, session, current_user.id)
    if not deleted:
        raise HTTPException(404, "Событие не найдено")
    return {"success": True}