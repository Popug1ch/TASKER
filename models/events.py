from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import date


class EventModel(Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str]
    event_date: Mapped[date]
