"""
Модель дедлайна (Deadline).

Дедлайн — задача с жёстким временем сгорания. Имеет момент создания
и флаг выполнения.
"""

from sqlalchemy.orm import Mapped, mapped_column
from core.database import Model
from datetime import datetime


class DeadlineModel(Model):
    """
    ORM-модель таблицы 'deadlines'.

    Атрибуты:
        id (int): первичный ключ.
        user_id (int): ID пользователя (индексирован).
        name (str): название дедлайна.
        deadline_time (datetime): дата и время, до которого нужно выполнить.
        created_at (datetime): момент создания (по умолчанию текущее время).
        is_completed (bool): выполнен ли дедлайн.
    """
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_id: Mapped[int] = mapped_column(index=True)
    """Владелец дедлайна. Индекс для быстрого поиска по пользователю."""

    name: Mapped[str]
    """Название дедлайна (обязательное)."""

    deadline_time: Mapped[datetime]
    """Крайний срок (дата и время). Используется для расчёта оставшегося времени."""

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    """Время создания дедлайна (автоматически проставляется при вставке)."""

    is_completed: Mapped[bool] = mapped_column(default=False)
    """Флаг выполнения (True — дедлайн закрыт)."""