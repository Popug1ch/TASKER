"""
Схемы для работы с задачами (tasks).
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class STaskIn(BaseModel):
    """
    Базовая схема задачи.

    Атрибуты:
        name (str): название задачи.
        start_time (datetime): дата и время начала.
        end_time (datetime): дата и время окончания.
        category (str): категория задачи.
        priority (str): приоритет (Низкая, Средняя, Высокая, Очень высокая).
        is_completed (bool): флаг выполнения (по умолчанию False).
    """

    name: str
    start_time: datetime
    end_time: datetime
    category: str
    priority: str
    is_completed: bool = False


class STaskAdd(STaskIn):
    """Схема для создания новой задачи (псевдоним)."""

    pass


class STaskUpdate(STaskIn):
    """Схема для обновления задачи (псевдоним)."""

    pass


class STask(STaskIn):
    """
    Схема для ответа с данными задачи.

    Атрибуты:
        id (int): идентификатор задачи.
        duration (int): длительность в минутах (вычисляется на сервере).
    """

    id: int
    duration: int

    model_config = ConfigDict(from_attributes=True)
    """Разрешает создание схемы из ORM-объекта."""
