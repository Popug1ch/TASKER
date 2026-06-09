"""
Схемы для работы с дедлайнами (deadlines).
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DeadlineIn(BaseModel):
    """
    Базовая схема дедлайна (входные данные).

    Атрибуты:
        name (str): название дедлайна.
        deadline_time (datetime): дата и время сгорания.
        is_completed (bool): флаг выполнения (по умолчанию False).
    """

    name: str
    deadline_time: datetime
    is_completed: bool = False


class DeadlineAdd(DeadlineIn):
    """Схема для создания нового дедлайна (псевдоним)."""

    pass


class DeadlineUpdate(DeadlineIn):
    """Схема для обновления дедлайна (псевдоним)."""

    pass


class Deadline(DeadlineIn):
    """
    Схема для ответа с данными дедлайна (включая id и created_at).

    Атрибуты:
        id (int): идентификатор дедлайна.
        created_at (datetime): дата и время создания.
    """

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    """Разрешает создание схемы из ORM-объекта (SQLAlchemy)."""
