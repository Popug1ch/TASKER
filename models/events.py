"""
Модель события (Event).

Событие не имеет временно́го интервала — только дата (целый день).
Используется для отметки важных дат (встречи, праздники).
"""

from sqlalchemy.orm import Mapped, mapped_column
from core.database import Model
from datetime import date


class EventModel(Model):
    """
    ORM-модель таблицы 'events'.

    Атрибуты:
        id (int): первичный ключ.
        user_id (int): ID владельца события (индексирован).
        name (str): название события.
        event_date (date): дата события (без времени).
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_id: Mapped[int] = mapped_column(index=True)
    """ID пользователя, создавшего событие. Индекс для ускорения фильтрации."""

    name: Mapped[str]
    """Название события (например, 'День рождения', 'Конференция')."""

    event_date: Mapped[date]
    """Дата события (хранится только день, месяц, год)."""
