from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime


class DeadlineModel(Model):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str]
    deadline_time: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_completed: Mapped[bool] = mapped_column(default=False)
