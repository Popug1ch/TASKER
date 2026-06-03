from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.tasks import TasksModel
from schemas.task import STaskAdd, STaskUpdate


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
                TasksModel.start_time <= end_datetime,
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
