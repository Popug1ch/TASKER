"""
Модель сессии (Session).

Используется для хранения токенов аутентификации пользователей.
"""

from sqlalchemy.orm import Mapped, mapped_column
from core.database import Model
from datetime import datetime


class SessionModel(Model):
    """
    ORM-модель таблицы 'sessions'.

    Атрибуты:
        id (int): первичный ключ.
        user_id (int): ID пользователя.
        token (str): уникальный токен сессии (индексирован).
        expires_at (datetime): дата и время истечения сессии.
        created_at (datetime): момент создания сессии.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_id: Mapped[int] = mapped_column(index=True)
    """ID пользователя, которому принадлежит сессия. Индекс для быстрой фильтрации."""

    token: Mapped[str] = mapped_column(unique=True, index=True)
    """Уникальный токен (генерируется secrets.token_urlsafe). Индексирован для быстрого поиска."""

    expires_at: Mapped[datetime]
    """Время, после которого токен считается недействительным."""

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    """Дата и время создания сессии."""
