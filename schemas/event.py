"""
Схемы для работы с событиями (events).
"""

from pydantic import BaseModel, ConfigDict
from datetime import date


class EventIn(BaseModel):
    """
    Базовая схема события.

    Атрибуты:
        name (str): название события.
        event_date (date): дата события (без времени).
    """

    name: str
    event_date: date


class EventAdd(EventIn):
    """Схема для создания нового события (псевдоним)."""

    pass


class EventUpdate(EventIn):
    """Схема для обновления события (псевдоним)."""

    pass


class Event(EventIn):
    """
    Схема для ответа с данными события.

    Атрибуты:
        id (int): идентификатор события.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
    """Разрешает создание схемы из ORM-объекта."""
