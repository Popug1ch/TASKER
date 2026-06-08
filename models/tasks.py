from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime


class TasksModel(Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    duration: Mapped[int]
    category: Mapped[str]
    priority: Mapped[str]
    is_completed: Mapped[bool] = mapped_column(default=False)
