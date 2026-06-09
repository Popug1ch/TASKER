"""
Модель задачи (Task).

Хранит информацию о запланированных делах: название, временной интервал,
категорию, приоритет, статус выполнения, а также привязку к пользователю.
"""

from sqlalchemy.orm import Mapped, mapped_column
from core.database import Model
from datetime import datetime


class TasksModel(Model):
    """
    ORM-модель таблицы 'tasks'.

    Атрибуты:
        id (int): первичный ключ, автоинкремент.
        user_id (int): внешний ключ к таблице users (индексирован).
        name (str): название задачи.
        start_time (datetime): дата и время начала задачи.
        end_time (datetime): дата и время окончания задачи.
        duration (int): длительность в минутах (вычисляется автоматически).
        category (str): категория задачи (например, "Работа", "Учеба").
        priority (str): уровень важности (Низкая, Средняя, Высокая, Очень высокая).
        is_completed (bool): флаг выполнения задачи (по умолчанию False).
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    """Уникальный идентификатор задачи, генерируется БД."""

    user_id: Mapped[int] = mapped_column(index=True)
    """ID пользователя-владельца задачи. Индексируется для быстрых запросов."""

    name: Mapped[str]
    """Название задачи (обязательное поле)."""

    start_time: Mapped[datetime]
    """Дата и время начала выполнения задачи."""

    end_time: Mapped[datetime]
    """Дата и время окончания задачи (должно быть позже start_time)."""

    duration: Mapped[int]
    """Длительность задачи в минутах, вычисляется как (end_time - start_time)."""

    category: Mapped[str]
    """Произвольная категория (строка), может быть пустой."""

    priority: Mapped[str]
    """Приоритет: 'Низкая', 'Средняя', 'Высокая' или 'Очень высокая'."""

    is_completed: Mapped[bool] = mapped_column(default=False)
    """Флаг, указывающий, выполнена ли задача."""
