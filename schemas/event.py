from pydantic import BaseModel, ConfigDict
from datetime import date


class EventIn(BaseModel):
    name: str
    event_date: date


class EventAdd(EventIn):
    pass


class EventUpdate(EventIn):
    pass


class Event(EventIn):
    id: int
    model_config = ConfigDict(from_attributes=True)
