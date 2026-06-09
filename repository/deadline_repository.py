"""
Модуль репозитория для работы с дедлайнами (Deadlines).
Дедлайны имеют дату и время сгорания, флаг is_completed.
"""

from datetime import datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.deadline import DeadlineModel
from schemas.deadline import DeadlineAdd, DeadlineUpdate


class DeadlineRepository:
    """
    Репозиторий для операций с дедлайнами пользователя.
    """

    @classmethod
    async def add_one(
        cls, data: DeadlineAdd, session: AsyncSession, user_id: int
    ) -> DeadlineModel:
        """
        Создаёт новый дедлайн.

        Параметры:
            data (DeadlineAdd): схема с данными дедлайна.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            DeadlineModel: созданный дедлайн.
        """
        deadline = DeadlineModel(
            name=data.name,
            deadline_time=data.deadline_time,
            created_at=datetime.now(),
            is_completed=False,
            user_id=user_id,
        )
        session.add(deadline)
        await session.commit()
        await session.refresh(deadline)
        return deadline

    @classmethod
    async def find_by_date(
        cls, session: AsyncSession, target_date: datetime, user_id: int
    ) -> list[DeadlineModel]:
        """
        Возвращает дедлайны, приходящиеся на конкретную дату (с учётом времени).

        Параметры:
            session (AsyncSession): сессия БД.
            target_date (datetime): дата/время (берётся только дата).
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[DeadlineModel]: список дедлайнов.
        """
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        stmt = select(DeadlineModel).where(
            DeadlineModel.user_id == user_id,
            DeadlineModel.deadline_time >= start_of_day,
            DeadlineModel.deadline_time <= end_of_day,
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def find_all(cls, session: AsyncSession, user_id: int) -> list[DeadlineModel]:
        """
        Возвращает все дедлайны пользователя (включая выполненные).

        Параметры:
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[DeadlineModel]: все дедлайны.
        """
        stmt = (
            select(DeadlineModel)
            .where(DeadlineModel.user_id == user_id)
            .order_by(DeadlineModel.deadline_time.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def find_active(
        cls, session: AsyncSession, user_id: int
    ) -> list[DeadlineModel]:
        """
        Возвращает только активные (невыполненные) дедлайны.

        Параметры:
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[DeadlineModel]: активные дедлайны.
        """
        stmt = (
            select(DeadlineModel)
            .where(
                DeadlineModel.user_id == user_id, DeadlineModel.is_completed == False
            )
            .order_by(DeadlineModel.deadline_time.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_deadline(
        cls, deadline_id: int, data: DeadlineUpdate, session: AsyncSession, user_id: int
    ) -> DeadlineModel | None:
        """
        Обновляет дедлайн (полное обновление).

        Параметры:
            deadline_id (int): идентификатор дедлайна.
            data (DeadlineUpdate): новые данные.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            DeadlineModel | None: обновлённый дедлайн или None.
        """
        update_data = data.model_dump()
        stmt = (
            update(DeadlineModel)
            .where(DeadlineModel.id == deadline_id, DeadlineModel.user_id == user_id)
            .values(**update_data)
            .returning(DeadlineModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def update_status(
        cls, deadline_id: int, is_completed: bool, session: AsyncSession, user_id: int
    ) -> DeadlineModel | None:
        """
        Обновляет только статус дедлайна (выполнен / не выполнен).

        Параметры:
            deadline_id (int): идентификатор дедлайна.
            is_completed (bool): новое состояние.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            DeadlineModel | None: обновлённый дедлайн или None.
        """
        stmt = (
            update(DeadlineModel)
            .where(DeadlineModel.id == deadline_id, DeadlineModel.user_id == user_id)
            .values(is_completed=is_completed)
            .returning(DeadlineModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def delete_deadline(
        cls, deadline_id: int, session: AsyncSession, user_id: int
    ) -> bool:
        """
        Удаляет дедлайн.

        Параметры:
            deadline_id (int): идентификатор дедлайна.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            bool: True если удалён, иначе False.
        """
        stmt = delete(DeadlineModel).where(
            DeadlineModel.id == deadline_id, DeadlineModel.user_id == user_id
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def count_by_date(
        cls, session: AsyncSession, target_date: datetime, user_id: int
    ) -> int:
        """
        Подсчитывает количество дедлайнов на указанную дату (для ограничения 3 в день).

        Параметры:
            session (AsyncSession): сессия БД.
            target_date (datetime): дата.
            user_id (int): идентификатор пользователя.

        Возвращает:
            int: количество дедлайнов.
        """
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        stmt = (
            select(func.count())
            .select_from(DeadlineModel)
            .where(
                DeadlineModel.user_id == user_id,
                DeadlineModel.deadline_time >= start_of_day,
                DeadlineModel.deadline_time <= end_of_day,
            )
        )
        result = await session.execute(stmt)
        return result.scalar()

    @classmethod
    async def count_active(cls, session: AsyncSession, user_id: int) -> int:
        """
        Подсчитывает количество активных (невыполненных) дедлайнов.

        Параметры:
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            int: количество активных дедлайнов.
        """
        stmt = (
            select(func.count())
            .select_from(DeadlineModel)
            .where(
                DeadlineModel.user_id == user_id, DeadlineModel.is_completed == False
            )
        )
        result = await session.execute(stmt)
        return result.scalar()
