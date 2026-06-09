"""
Модель глобальных настроек (Settings).

Используется для хранения единственной записи с параметрами всего приложения
(например, дата начала текущей недели для механизма rollover).
"""

from sqlalchemy.orm import Mapped, mapped_column
from core.database import Model


class SettingsModel(Model):
    """
    ORM-модель таблицы 'settings'.

    Атрибуты:
        id (int): первичный ключ (всегда 1).
        current_week_start (str): дата начала текущей недели в ISO-формате.
    """
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    """Фиксированный идентификатор (всегда 1). Гарантирует единственность записи."""

    current_week_start: Mapped[str] = mapped_column(default="")
    """Дата понедельника текущей недели в формате ISO (YYYY-MM-DDTHH:MM:SS)."""