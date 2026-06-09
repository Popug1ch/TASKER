"""
Модуль репозитория для работы с пользователями (Users).
Включает хеширование паролей и поиск по email.
"""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import UserModel
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserRepository:
    """
    Репозиторий для операций с пользователями.
    """

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> UserModel | None:
        """
        Находит пользователя по email.

        Параметры:
            session (AsyncSession): сессия БД.
            email (str): адрес электронной почты.

        Возвращает:
            UserModel | None: объект пользователя или None.
        """
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create(
        cls, session: AsyncSession, username: str, email: str, password: str
    ) -> UserModel:
        """
        Создаёт нового пользователя с хешированным паролем.

        Параметры:
            session (AsyncSession): сессия БД.
            username (str): имя пользователя.
            email (str): email.
            password (str): пароль в открытом виде.

        Возвращает:
            UserModel: созданный пользователь.
        """
        hashed = pwd_context.hash(password)
        user = UserModel(
            username=username,
            email=email,
            hashed_password=hashed,
            created_at=datetime.now(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        """
        Проверяет соответствие пароля его хешу.

        Параметры:
            plain (str): пароль в открытом виде.
            hashed (str): хеш из базы данных.

        Возвращает:
            bool: True если пароль верен, иначе False.
        """
        return pwd_context.verify(plain, hashed)
