from datetime import datetime, timedelta, date
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.tasks import TasksModel
from models.settings import SettingsModel
from schemas.task import STaskAdd, STaskUpdate
from models.events import EventModel
from schemas.event import EventAdd, EventUpdate


class TaskRepository:
    @classmethod
    async def add_one(cls, data: STaskAdd, session: AsyncSession) -> TasksModel:
        duration = int((data.end_time - data.start_time).total_seconds() // 60)
        task_dict = data.model_dump()
        task = TasksModel(**task_dict, duration=duration, id=None)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    @classmethod
    async def find_all(cls, session: AsyncSession) -> list[TasksModel]:
        query = select(TasksModel).order_by(
            TasksModel.is_completed.asc(),
            TasksModel.start_time.asc(),
            TasksModel.duration.asc(),
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_in_range(
        cls, session: AsyncSession, start_datetime: datetime, end_datetime: datetime
    ) -> list[TasksModel]:
        query = (
            select(TasksModel)
            .where(
                TasksModel.start_time >= start_datetime,
                TasksModel.start_time
                < end_datetime,  # строго меньше, чтобы не дублировать
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
        cls, task_id: int, is_completed: bool, session: AsyncSession
    ) -> TasksModel | None:
        stmt = (
            update(TasksModel)
            .where(TasksModel.id == task_id)
            .values(is_completed=is_completed)
            .returning(TasksModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def update_task(
        cls, task_id: int, data: STaskUpdate, session: AsyncSession
    ) -> TasksModel | None:
        duration = int((data.end_time - data.start_time).total_seconds() // 60)
        update_data = data.model_dump()
        update_data["duration"] = duration
        stmt = (
            update(TasksModel)
            .where(TasksModel.id == task_id)
            .values(**update_data)
            .returning(TasksModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def delete_task(cls, task_id: int, session: AsyncSession) -> bool:
        stmt = delete(TasksModel).where(TasksModel.id == task_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def get_current_week_start(cls, session: AsyncSession) -> datetime:
        """Возвращает datetime понедельника текущей недели (начало дня)."""
        stmt = select(SettingsModel).where(SettingsModel.id == 1)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting and setting.current_week_start:
            return datetime.fromisoformat(setting.current_week_start)
        # Если нет настройки – инициализируем текущим понедельником
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
    async def set_current_week_start(cls, session: AsyncSession, new_start: datetime):
        stmt = (
            update(SettingsModel)
            .where(SettingsModel.id == 1)
            .values(current_week_start=new_start.isoformat())
        )
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def rollover_week(cls, session: AsyncSession):
        """
        Сдвигает незавершённые задачи текущей недели на следующую неделю (обновляя даты),
        удаляет задачи предыдущей недели, сдвигает текущую неделю.
        """
        current_start = await cls.get_current_week_start(session)
        current_end = current_start + timedelta(days=7)
        next_start = current_start + timedelta(days=7)
        prev_start = current_start - timedelta(days=7)

        # 1. Обновить незавершённые задачи текущей недели: увеличить даты на 7 дней
        stmt = select(TasksModel).where(
            TasksModel.start_time >= current_start,
            TasksModel.start_time < current_end,
            TasksModel.is_completed == False,
        )
        result = await session.execute(stmt)
        tasks_to_move = result.scalars().all()

        for task in tasks_to_move:
            task.start_time += timedelta(days=7)
            task.end_time += timedelta(days=7)
            # session.add(task) не нужен, объект уже привязан
        await session.flush()

        # 2. Удалить задачи предыдущей недели
        stmt = delete(TasksModel).where(
            TasksModel.start_time >= prev_start, TasksModel.start_time < current_start
        )
        await session.execute(stmt)

        # 3. Сдвинуть текущую неделю
        await cls.set_current_week_start(session, next_start)

        await session.commit()


class EventRepository:
    @classmethod
    async def add_one(cls, data: EventAdd, session: AsyncSession) -> EventModel:
        event = EventModel(**data.model_dump())
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @classmethod
    async def find_by_date(
        cls, session: AsyncSession, target_date: date
    ) -> list[EventModel]:
        stmt = select(EventModel).where(EventModel.event_date == target_date)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def find_all(cls, session: AsyncSession) -> list[EventModel]:
        stmt = select(EventModel)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_event(
        cls, event_id: int, data: EventUpdate, session: AsyncSession
    ) -> EventModel | None:
        stmt = (
            update(EventModel)
            .where(EventModel.id == event_id)
            .values(**data.model_dump())
            .returning(EventModel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def delete_event(cls, event_id: int, session: AsyncSession) -> bool:
        stmt = delete(EventModel).where(EventModel.id == event_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def count_by_date(cls, session: AsyncSession, target_date: date) -> int:
        stmt = (
            select(func.count())
            .select_from(EventModel)
            .where(EventModel.event_date == target_date)
        )
        result = await session.execute(stmt)
        return result.scalar()
