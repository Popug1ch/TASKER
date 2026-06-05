from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime


class DeadlineModel(Model):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str]
    deadline_time: Mapped[datetime]
    is_completed: Mapped[bool] = mapped_column(default=False)
