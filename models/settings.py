from sqlalchemy.orm import Mapped, mapped_column
from database import Model


class SettingsModel(Model):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    current_week_start: Mapped[str] = mapped_column(default="")
