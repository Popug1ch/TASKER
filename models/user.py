"""
Модель пользователя (User).

Содержит учётные данные, хеш пароля, привязку к Telegram.
"""

from sqlalchemy.orm import Mapped, mapped_column
from core.database import Model
from datetime import datetime


class UserModel(Model):
    """
    ORM-модель таблицы 'users'.

    Атрибуты:
        id (int): первичный ключ.
        username (str): уникальное имя пользователя.
        email (str): уникальный email (используется для входа).
        hashed_password (str): хеш пароля (алгоритм pbkdf2_sha256).
        telegram_id (int | None): ID в Telegram (для привязки бота).
        created_at (datetime): дата регистрации.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    username: Mapped[str] = mapped_column(unique=True)
    """Уникальное отображаемое имя пользователя."""

    email: Mapped[str] = mapped_column(unique=True)
    """Email пользователя, используется как логин. Также должен быть уникальным."""

    hashed_password: Mapped[str]
    """Хеш пароля, сгенерированный passlib (pbkdf2_sha256)."""

    telegram_id: Mapped[int] = mapped_column(nullable=True, unique=True, default=None)
    """ID чата пользователя в Telegram для отправки уведомлений (опционально)."""

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    """Дата и время регистрации аккаунта."""