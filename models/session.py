from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import datetime

class SessionModel(Model):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)