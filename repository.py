from datetime import datetime, timedelta, date
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.tasks import TasksModel
from models.settings import SettingsModel
from schemas.task import STaskAdd, STaskUpdate
from models.events import EventModel
from schemas.event import EventAdd, EventUpdate
from models.deadline import DeadlineModel
from schemas.deadline import DeadlineUpdate, DeadlineAdd
from models.user import UserModel
from models.session import SessionModel
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ---------- TaskRepository ----------
class TaskRepository:
    @classmethod
    async def add_one(cls, data: STaskAdd, session: AsyncSession, user_id: int) -> TasksModel:
        duration = int((data.end_time - data.start_time).total_seconds() // 60)
        task_dict = data.model_dump()
        task = TasksModel(**task_dict, duration=duration, user_id=user_id)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    @classmethod
    async def find_all(cls, session: AsyncSession, user_id: int) -> list[TasksModel]:
        query = select(TasksModel).where(TasksModel.user_id == user_id).order_by(
            TasksModel.is_completed.asc(),
            TasksModel.start_time.asc(),
            TasksModel.duration.asc(),
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_in_range(
        cls, session: AsyncSession, start_datetime: datetime, end_datetime: datetime, user_id: int
    ) -> list[TasksModel]:
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
    async def delete_task(cls, task_id: int, session: AsyncSession, user_id: int) -> bool:
        stmt = delete(TasksModel).where(TasksModel.id == task_id, TasksModel.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def get_current_week_start(cls, session: AsyncSession) -> datetime:
        """Глобальная настройка (без привязки к пользователю)."""
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
    async def set_current_week_start(cls, session: AsyncSession, new_start: datetime):
        stmt = update(SettingsModel).where(SettingsModel.id == 1).values(current_week_start=new_start.isoformat())
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def rollover_week(cls, session: AsyncSession):
        current_start = await cls.get_current_week_start(session)
        current_end = current_start + timedelta(days=7)
        next_start = current_start + timedelta(days=7)
        prev_start = current_start - timedelta(days=7)

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
        await session.flush()

        stmt = delete(TasksModel).where(
            TasksModel.start_time >= prev_start, TasksModel.start_time < current_start
        )
        await session.execute(stmt)

        await cls.set_current_week_start(session, next_start)
        await session.commit()

# ---------- EventRepository ----------
class EventRepository:
    @classmethod
    async def add_one(cls, data: EventAdd, session: AsyncSession, user_id: int) -> EventModel:
        event = EventModel(**data.model_dump(), user_id=user_id)
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @classmethod
    async def find_by_date(cls, session: AsyncSession, target_date: date, user_id: int) -> list[EventModel]:
        stmt = select(EventModel).where(EventModel.event_date == target_date, EventModel.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def find_all(cls, session: AsyncSession, user_id: int) -> list[EventModel]:
        stmt = select(EventModel).where(EventModel.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_event(cls, event_id: int, data: EventUpdate, session: AsyncSession, user_id: int) -> EventModel | None:
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
    async def delete_event(cls, event_id: int, session: AsyncSession, user_id: int) -> bool:
        stmt = delete(EventModel).where(EventModel.id == event_id, EventModel.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def count_by_date(cls, session: AsyncSession, target_date: date, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(EventModel)
            .where(EventModel.event_date == target_date, EventModel.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar()

# ---------- DeadlineRepository ----------
class DeadlineRepository:
    @classmethod
    async def add_one(cls, data: DeadlineAdd, session: AsyncSession, user_id: int) -> DeadlineModel:
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
    async def find_by_date(cls, session: AsyncSession, target_date: datetime, user_id: int) -> list[DeadlineModel]:
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
        stmt = select(DeadlineModel).where(DeadlineModel.user_id == user_id).order_by(DeadlineModel.deadline_time.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def find_active(cls, session: AsyncSession, user_id: int) -> list[DeadlineModel]:
        stmt = (
            select(DeadlineModel)
            .where(DeadlineModel.user_id == user_id, DeadlineModel.is_completed == False)
            .order_by(DeadlineModel.deadline_time.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_deadline(cls, deadline_id: int, data: DeadlineUpdate, session: AsyncSession, user_id: int) -> DeadlineModel | None:
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
    async def update_status(cls, deadline_id: int, is_completed: bool, session: AsyncSession, user_id: int) -> DeadlineModel | None:
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
    async def delete_deadline(cls, deadline_id: int, session: AsyncSession, user_id: int) -> bool:
        stmt = delete(DeadlineModel).where(DeadlineModel.id == deadline_id, DeadlineModel.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    @classmethod
    async def count_by_date(cls, session: AsyncSession, target_date: datetime, user_id: int) -> int:
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
        stmt = (
            select(func.count())
            .select_from(DeadlineModel)
            .where(DeadlineModel.user_id == user_id, DeadlineModel.is_completed == False)
        )
        result = await session.execute(stmt)
        return result.scalar()

# ---------- UserRepository и SessionRepository ----------
class UserRepository:
    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, session: AsyncSession, username: str, email: str, password: str) -> UserModel:
        hashed = pwd_context.hash(password)
        user = UserModel(
            username=username,
            email=email,
            hashed_password=hashed,
            created_at=datetime.now()
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

class SessionRepository:
    @classmethod
    async def create(cls, session: AsyncSession, user_id: int, expires_days: int = 30) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=expires_days)
        sess = SessionModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            created_at=datetime.now()
        )
        session.add(sess)
        await session.commit()
        return token

    @classmethod
    async def get_user_by_token(cls, session: AsyncSession, token: str) -> UserModel | None:
        stmt = select(SessionModel).where(SessionModel.token == token, SessionModel.expires_at > datetime.now())
        result = await session.execute(stmt)
        sess = result.scalar_one_or_none()
        if not sess:
            return None
        stmt = select(UserModel).where(UserModel.id == sess.user_id)
        user_result = await session.execute(stmt)
        return user_result.scalar_one_or_none()

    @classmethod
    async def delete(cls, session: AsyncSession, token: str):
        stmt = delete(SessionModel).where(SessionModel.token == token)
        await session.execute(stmt)
        await session.commit()