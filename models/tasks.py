from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime


class TasksModel(Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  # Название
    start_time: Mapped[datetime]  # Начало выполнения
    end_time: Mapped[datetime]  # Конец выполнения
    duration: Mapped[int]  # Длительность в минутах
    category: Mapped[str]  # Категория
    priority: Mapped[str]  # Важность (Низкая, Средняя, Высокая, Очень высокая)
    is_completed: Mapped[bool] = mapped_column(default=False)  # Состояние
