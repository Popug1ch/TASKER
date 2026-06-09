"""
Модуль репозитория для работы с сессиями (Sessions).
Управляет токенами аутентификации и их временем жизни.
"""

from datetime import datetime, timedelta
import secrets
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.session import SessionModel
from models.user import UserModel


class SessionRepository:
    """
    Репозиторий для операций с сессиями (токенами).
    """

    @classmethod
    async def create(
        cls, session: AsyncSession, user_id: int, expires_days: int = 30
    ) -> str:
        """
        Создаёт новую сессию для пользователя.

        Параметры:
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.
            expires_days (int): срок действия сессии в днях (по умолчанию 30).

        Возвращает:
            str: уникальный токен сессии.
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=expires_days)
        sess = SessionModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            created_at=datetime.now(),
        )
        session.add(sess)
        await session.commit()
        return token

    @classmethod
    async def get_user_by_token(
        cls, session: AsyncSession, token: str
    ) -> UserModel | None:
        """
        Находит пользователя по токену сессии (с проверкой срока действия).

        Параметры:
            session (AsyncSession): сессия БД.
            token (str): токен сессии.

        Возвращает:
            UserModel | None: пользователь, если сессия активна, иначе None.
        """
        stmt = select(SessionModel).where(
            SessionModel.token == token, SessionModel.expires_at > datetime.now()
        )
        result = await session.execute(stmt)
        sess = result.scalar_one_or_none()
        if not sess:
            return None
        stmt = select(UserModel).where(UserModel.id == sess.user_id)
        user_result = await session.execute(stmt)
        return user_result.scalar_one_or_none()

    @classmethod
    async def delete(cls, session: AsyncSession, token: str) -> None:
        """
        Удаляет сессию (выход пользователя).

        Параметры:
            session (AsyncSession): сессия БД.
            token (str): токен сессии.
        """
        stmt = delete(SessionModel).where(SessionModel.token == token)
        await session.execute(stmt)
        await session.commit()
