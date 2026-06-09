from datetime import datetime, timedelta
from models.user import UserModel
from models.tasks import TasksModel
from models.events import EventModel
from models.deadline import DeadlineModel
from repository import UserRepository

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import DATABASE_URL, Model

# Синхронный движок
sync_engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""))
SyncSession = sessionmaker(sync_engine)

# Создаём таблицы, если их нет (один раз при импорте)
Model.metadata.create_all(sync_engine)


def get_user_by_telegram_id(telegram_id: int):
    """Получить пользователя по telegram_id"""
    with SyncSession() as session:
        return (
            session.query(UserModel)
            .filter(UserModel.telegram_id == telegram_id)
            .first()
        )


def register_user_by_email_password(
    telegram_id: int, email: str, password: str
) -> bool:
    """Привязать telegram_id к существующему пользователю по email и паролю"""
    with SyncSession() as session:
        user = session.query(UserModel).filter(UserModel.email == email).first()
        if not user or not UserRepository.verify_password(
            password, user.hashed_password
        ):
            return False
        user.telegram_id = telegram_id
        session.commit()
        return True


def get_today_tasks(user_id: int):
    """Получить все задачи пользователя на сегодня (невыполненные + выполненные)"""
    with SyncSession() as session:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return (
            session.query(TasksModel)
            .filter(
                TasksModel.user_id == user_id,
                TasksModel.start_time >= today_start,
                TasksModel.start_time < today_end,
            )
            .order_by(TasksModel.start_time)
            .all()
        )


def get_today_events(user_id: int):
    """Получить все события пользователя на сегодня"""
    with SyncSession() as session:
        today = datetime.now().date()
        return (
            session.query(EventModel)
            .filter(EventModel.user_id == user_id, EventModel.event_date == today)
            .all()
        )


def get_upcoming_deadlines(user_id: int):
    """Получить дедлайны пользователя на ближайшие 24 часа (невыполненные)"""
    with SyncSession() as session:
        now = datetime.now()
        day_later = now + timedelta(days=1)
        return (
            session.query(DeadlineModel)
            .filter(
                DeadlineModel.user_id == user_id,
                DeadlineModel.is_completed == False,
                DeadlineModel.deadline_time > now,
                DeadlineModel.deadline_time <= day_later,
            )
            .order_by(DeadlineModel.deadline_time)
            .all()
        )


def get_all_users_with_telegram():
    """Получить всех пользователей, у которых есть telegram_id (для рассылки уведомлений)"""
    with SyncSession() as session:
        return session.query(UserModel).filter(UserModel.telegram_id.isnot(None)).all()


def mark_task_complete(task_id: int, user_id: int) -> bool:
    """Отметить задачу как выполненную"""
    with SyncSession() as session:
        task = (
            session.query(TasksModel)
            .filter(TasksModel.id == task_id, TasksModel.user_id == user_id)
            .first()
        )
        if task and not task.is_completed:
            task.is_completed = True
            session.commit()
            return True
        return False


def get_uncompleted_tasks_for_today(user_id: int):
    """Получить только невыполненные задачи на сегодня"""
    with SyncSession() as session:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return (
            session.query(TasksModel)
            .filter(
                TasksModel.user_id == user_id,
                TasksModel.is_completed == False,
                TasksModel.start_time >= today_start,
                TasksModel.start_time < today_end,
            )
            .order_by(TasksModel.start_time)
            .all()
        )


def get_upcoming_tasks_for_notification():
    """Возвращает список (telegram_id, task_name, start_time) для задач, начинающихся через 5–15 минут."""
    with SyncSession() as session:
        now = datetime.now()
        start_window = now + timedelta(minutes=5)
        end_window = now + timedelta(minutes=15)
        tasks = (
            session.query(TasksModel)
            .filter(
                TasksModel.is_completed == False,
                TasksModel.start_time >= start_window,
                TasksModel.start_time <= end_window,
            )
            .all()
        )
        result = []
        for task in tasks:
            user = session.query(UserModel).filter(UserModel.id == task.user_id).first()
            if user and user.telegram_id:
                result.append((user.telegram_id, task.name, task.start_time))
        print(f"[db_helpers] Найдено задач для уведомления: {len(result)}")
        return result


def get_deadlines_for_notification():
    """
    Получить дедлайны, которые наступают через 24, 12, 3, 1 час (для отправки уведомлений).
    Возвращает список кортежей (telegram_id, deadline_name, hours_left).
    """
    with SyncSession() as session:
        now = datetime.now()
        deadlines = (
            session.query(DeadlineModel)
            .filter(
                DeadlineModel.is_completed == False, DeadlineModel.deadline_time > now
            )
            .all()
        )
        result = []
        for dl in deadlines:
            delta = dl.deadline_time - now
            hours_left = delta.total_seconds() / 3600
            if 23.5 <= hours_left <= 24.5:
                hours = 24
            elif 11.5 <= hours_left <= 12.5:
                hours = 12
            elif 2.5 <= hours_left <= 3.5:
                hours = 3
            elif 0.5 <= hours_left <= 1.5:
                hours = 1
            else:
                continue
            user = session.query(UserModel).filter(UserModel.id == dl.user_id).first()
            if user and user.telegram_id:
                result.append((user.telegram_id, dl.name, hours))
        print(f"[db_helpers] Найдено дедлайнов для уведомления: {len(result)}")
        return result


def get_today_events_for_notification():
    """
    Получить события на сегодня (отправлять утром около 9:00).
    Возвращает список кортежей (telegram_id, event_name).
    """
    with SyncSession() as session:
        today = datetime.now().date()
        events = session.query(EventModel).filter(EventModel.event_date == today).all()
        result = []
        for ev in events:
            user = session.query(UserModel).filter(UserModel.id == ev.user_id).first()
            if user and user.telegram_id:
                result.append((user.telegram_id, ev.name))
        return result
