"""
Модуль репозитория для работы с событиями (Events).
События не имеют времени, только дату.
"""

from datetime import date
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.events import EventModel
from schemas.event import EventAdd, EventUpdate


class EventRepository:
    """
    Репозиторий для операций с событиями пользователя.
    """

    @classmethod
    async def add_one(
        cls, data: EventAdd, session: AsyncSession, user_id: int
    ) -> EventModel:
        """
        Создаёт новое событие.

        Параметры:
            data (EventAdd): схема с данными события.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            EventModel: созданное событие.
        """
        event = EventModel(**data.model_dump(), user_id=user_id)
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @classmethod
    async def find_by_date(
        cls, session: AsyncSession, target_date: date, user_id: int
    ) -> list[EventModel]:
        """
        Возвращает события на конкретную дату.

        Параметры:
            session (AsyncSession): сессия БД.
            target_date (date): дата.
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[EventModel]: список событий.
        """
        stmt = select(EventModel).where(
            EventModel.event_date == target_date, EventModel.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def find_all(cls, session: AsyncSession, user_id: int) -> list[EventModel]:
        """
        Возвращает все события пользователя.

        Параметры:
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[EventModel]: все события.
        """
        stmt = select(EventModel).where(EventModel.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_event(
        cls, event_id: int, data: EventUpdate, session: AsyncSession, user_id: int
    ) -> EventModel | None:
        """
        Обновляет событие.

        Параметры:
            event_id (int): идентификатор события.
            data (EventUpdate): новые данные.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            EventModel | None: обновлённое событие или None.
        """
        stmt = (
            update(EventModel)
            .where(EventModel.id == event_id, EventModel.user_id == user_id)
            .values(**data.model_dump())
            .returning(EventModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def delete_event(
        cls, event_id: int, session: AsyncSession, user_id: int
    ) -> bool:
        """
        Удаляет событие.

        Параметры:
            event_id (int): идентификатор события.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            bool: True если удалено, иначе False.
        """
        stmt = delete(EventModel).where(
            EventModel.id == event_id, EventModel.user_id == user_id
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def count_by_date(
        cls, session: AsyncSession, target_date: date, user_id: int
    ) -> int:
        """
        Подсчитывает количество событий на указанную дату (для ограничения 3 в день).

        Параметры:
            session (AsyncSession): сессия БД.
            target_date (date): дата.
            user_id (int): идентификатор пользователя.

        Возвращает:
            int: количество событий.
        """
        stmt = (
            select(func.count())
            .select_from(EventModel)
            .where(EventModel.event_date == target_date, EventModel.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar()
