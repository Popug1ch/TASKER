import schedule
import threading
import time
from datetime import datetime
from bot.loader import bot
from bot.utils.db_helpers import (
    get_upcoming_tasks_for_notification,
    get_deadlines_for_notification,
    get_today_events_for_notification
)

def send_notifications():
    print("[scheduler] Проверка уведомлений...")
    # Задачи (5–15 минут до начала)
    tasks_to_notify = get_upcoming_tasks_for_notification()
    for tg_id, task_name, start_time in tasks_to_notify:
        try:
            bot.send_message(tg_id, f"🔔 Напоминание: задача «{task_name}» начинается в {start_time.strftime('%H:%M')}!")
            print(f"[scheduler] Отправлено уведомление пользователю {tg_id} о задаче {task_name}")
        except Exception as e:
            print(f"[scheduler] Ошибка отправки {tg_id}: {e}")

    # Дедлайны (24, 12, 3, 1 час)
    deadlines = get_deadlines_for_notification()
    for tg_id, dl_name, hours in deadlines:
        try:
            bot.send_message(tg_id, f"⚠️ До дедлайна «{dl_name}» осталось {hours} часа/часов!")
            print(f"[scheduler] Отправлено уведомление о дедлайне {dl_name} пользователю {tg_id}")
        except Exception as e:
            print(f"[scheduler] Ошибка отправки {tg_id}: {e}")

    # События (один раз утром около 9:00)
    current_hour = datetime.now().hour
    if 9 <= current_hour < 10 and not hasattr(send_notifications, "events_sent_today"):
        events = get_today_events_for_notification()
        for tg_id, event_name in events:
            try:
                bot.send_message(tg_id, f"📅 Сегодня событие: {event_name}")
            except Exception as e:
                print(f"[scheduler] Ошибка отправки события: {e}")
        send_notifications.events_sent_today = True
    elif current_hour != 9:
        send_notifications.events_sent_today = False

def run_scheduler():
    schedule.every(2).minutes.do(send_notifications)
    while True:
        schedule.run_pending()
        time.sleep(30)

def start_scheduler():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    print("[scheduler] Планировщик запущен")