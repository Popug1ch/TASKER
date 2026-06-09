"""
Модуль репозитория для работы с задачами (Tasks).
Содержит CRUD операции и вспомогательные методы для задач,
а также глобальные настройки недель (rollover).
"""

from datetime import datetime, timedelta
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.tasks import TasksModel
from models.settings import SettingsModel
from schemas.task import STaskAdd, STaskUpdate


class TaskRepository:
    """
    Репозиторий для операций с задачами пользователя.
    Все методы принимают user_id для изоляции данных между пользователями.
    """

    @classmethod
    async def add_one(
        cls, data: STaskAdd, session: AsyncSession, user_id: int
    ) -> TasksModel:
        """
        Создаёт новую задачу.

        Параметры:
            data (STaskAdd): Pydantic-схема с данными задачи.
            session (AsyncSession): асинхронная сессия SQLAlchemy.
            user_id (int): идентификатор текущего пользователя.

        Возвращает:
            TasksModel: созданный объект задачи с заполненными полями (включая id).
        """
        duration = int((data.end_time - data.start_time).total_seconds() // 60)
        task_dict = data.model_dump()
        task = TasksModel(**task_dict, duration=duration, user_id=user_id)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    @classmethod
    async def find_all(cls, session: AsyncSession, user_id: int) -> list[TasksModel]:
        """
        Возвращает все задачи пользователя (без фильтра по дате).

        Параметры:
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[TasksModel]: список задач, отсортированный по статусу, времени начала и длительности.
        """
        query = (
            select(TasksModel)
            .where(TasksModel.user_id == user_id)
            .order_by(
                TasksModel.is_completed.asc(),
                TasksModel.start_time.asc(),
                TasksModel.duration.asc(),
            )
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_in_range(
        cls,
        session: AsyncSession,
        start_datetime: datetime,
        end_datetime: datetime,
        user_id: int,
    ) -> list[TasksModel]:
        """
        Возвращает задачи, попадающие в указанный временной диапазон.

        Параметры:
            session (AsyncSession): сессия БД.
            start_datetime (datetime): начало диапазона.
            end_datetime (datetime): конец диапазона (не включая).
            user_id (int): идентификатор пользователя.

        Возвращает:
            list[TasksModel]: список задач в диапазоне.
        """
        query = (
            select(TasksModel)
            .where(
                TasksModel.user_id == user_id,
                TasksModel.start_time >= start_datetime,
                TasksModel.start_time < end_datetime,
            )
            .order_by(
                TasksModel.is_completed.asc(),
                TasksModel.start_time.asc(),
                TasksModel.duration.asc(),
            )
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def update_status(
        cls, task_id: int, is_completed: bool, session: AsyncSession, user_id: int
    ) -> TasksModel | None:
        """
        Обновляет статус задачи (выполнена / не выполнена).

        Параметры:
            task_id (int): идентификатор задачи.
            is_completed (bool): новое состояние.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя (проверка прав).

        Возвращает:
            TasksModel | None: обновлённая задача или None, если задача не найдена.
        """
        stmt = (
            update(TasksModel)
            .where(TasksModel.id == task_id, TasksModel.user_id == user_id)
            .values(is_completed=is_completed)
            .returning(TasksModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def update_task(
        cls, task_id: int, data: STaskUpdate, session: AsyncSession, user_id: int
    ) -> TasksModel | None:
        """
        Полное обновление задачи (изменяет все поля).

        Параметры:
            task_id (int): идентификатор задачи.
            data (STaskUpdate): новые данные.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            TasksModel | None: обновлённая задача или None.
        """
        duration = int((data.end_time - data.start_time).total_seconds() // 60)
        update_data = data.model_dump()
        update_data["duration"] = duration
        stmt = (
            update(TasksModel)
            .where(TasksModel.id == task_id, TasksModel.user_id == user_id)
            .values(**update_data)
            .returning(TasksModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def delete_task(
        cls, task_id: int, session: AsyncSession, user_id: int
    ) -> bool:
        """
        Удаляет задачу.

        Параметры:
            task_id (int): идентификатор задачи.
            session (AsyncSession): сессия БД.
            user_id (int): идентификатор пользователя.

        Возвращает:
            bool: True если удалена, иначе False.
        """
        stmt = delete(TasksModel).where(
            TasksModel.id == task_id, TasksModel.user_id == user_id
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def get_current_week_start(cls, session: AsyncSession) -> datetime:
        """
        Возвращает дату понедельника текущей (активной) недели.
        Используется для механизма переноса задач (rollover).

        Параметры:
            session (AsyncSession): сессия БД.

        Возвращает:
            datetime: дата и время начала недели (00:00:00 понедельника).
        """
        stmt = select(SettingsModel).where(SettingsModel.id == 1)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting and setting.current_week_start:
            return datetime.fromisoformat(setting.current_week_start)

        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, datetime.min.time())
        if not setting:
            setting = SettingsModel(id=1, current_week_start=start.isoformat())
            session.add(setting)
        else:
            setting.current_week_start = start.isoformat()
        await session.commit()
        return start

    @classmethod
    async def set_current_week_start(
        cls, session: AsyncSession, new_start: datetime
    ) -> None:
        """
        Устанавливает новую дату начала текущей недели.

        Параметры:
            session (AsyncSession): сессия БД.
            new_start (datetime): новый понедельник.
        """
        stmt = (
            update(SettingsModel)
            .where(SettingsModel.id == 1)
            .values(current_week_start=new_start.isoformat())
        )
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def rollover_week(cls, session: AsyncSession) -> None:
        """
        Выполняет перенос незавершённых задач текущей недели на следующую неделю,
        удаляет задачи предыдущей недели и сдвигает глобальную дату начала недели.
        Используется в жизненном цикле приложения.
        """
        current_start = await cls.get_current_week_start(session)
        current_end = current_start + timedelta(days=7)
        next_start = current_start + timedelta(days=7)
        prev_start = current_start - timedelta(days=7)

        # 1. Найти незавершённые задачи текущей недели
        stmt = select(TasksModel).where(
            TasksModel.start_time >= current_start,
            TasksModel.start_time < current_end,
            TasksModel.is_completed == False,
        )
        result = await session.execute(stmt)
        tasks_to_move = result.scalars().all()

        # 2. Сдвинуть их даты на 7 дней вперёд
        for task in tasks_to_move:
            task.start_time += timedelta(days=7)
            task.end_time += timedelta(days=7)
        await session.flush()

        # 3. Удалить все задачи предыдущей недели
        stmt = delete(TasksModel).where(
            TasksModel.start_time >= prev_start, TasksModel.start_time < current_start
        )
        await session.execute(stmt)

        # 4. Сдвинуть глобальную неделю
        await cls.set_current_week_start(session, next_start)
        await session.commit()
