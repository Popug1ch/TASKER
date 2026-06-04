from fastapi import APIRouter, HTTPException, status
from database import SessionDep
from models.events import EventModel
from schemas.event import Event, EventAdd, EventUpdate
from repository import EventRepository
from datetime import date

router = APIRouter(prefix="/api/events", tags=["События"])


@router.get("/all")
async def get_all_events(session: SessionDep):
    events = await EventRepository.find_all(session)
    return events


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventAdd, session: SessionDep):
    # Проверка на максимум 3 события в день
    count = await EventRepository.count_by_date(session, event.event_date)
    if count >= 3:
        raise HTTPException(400, "В этот день уже есть 3 события")
    return await EventRepository.add_one(event, session)


@router.get("/{event_date}")
async def get_events_by_date(event_date: date, session: SessionDep):
    events = await EventRepository.find_by_date(session, event_date)
    return events


@router.put("/{event_id}", response_model=Event)
async def update_event(event_id: int, event_data: EventUpdate, session: SessionDep):
    # При смене даты нужно перепроверить лимит
    if event_data.event_date:
        count = await EventRepository.count_by_date(session, event_data.event_date)
        # если событие перемещается на другой день, и там уже 3, то запретить
        # но сначала получим старое событие, чтобы не считать его же
        old_event = await session.get(EventModel, event_id)
        if old_event and old_event.event_date != event_data.event_date:
            if count >= 3:
                raise HTTPException(400, "В этот день уже есть 3 события")
    updated = await EventRepository.update_event(event_id, event_data, session)
    if not updated:
        raise HTTPException(404, "Событие не найдено")
    return updated


@router.delete("/{event_id}")
async def delete_event(event_id: int, session: SessionDep):
    deleted = await EventRepository.delete_event(event_id, session)
    if not deleted:
        raise HTTPException(404, "Событие не найдено")
    return {"success": True}
