from telebot.types import Message, CallbackQuery
from bot.loader import bot
from bot.utils.db_helpers import (
    get_user_by_telegram_id,
    get_today_tasks,
    get_uncompleted_tasks_for_today,
    mark_task_complete
)
from bot.keyboards.inline_keyboards import get_complete_task_keyboard

@bot.message_handler(commands=['tasks'])
def show_tasks(message: Message):
    user = get_user_by_telegram_id(message.chat.id)
    if not user:
        bot.reply_to(message, "❌ Сначала зарегистрируйтесь через /register")
        return

    tasks = get_today_tasks(user.id)
    if not tasks:
        bot.send_message(message.chat.id, "📭 На сегодня нет задач.")
        return

    msg = "📋 *Задачи на сегодня:*\n\n"
    for t in tasks:
        status = "✅" if t.is_completed else "⏳"
        time_str = f"{t.start_time.strftime('%H:%M')}–{t.end_time.strftime('%H:%M')}"
        msg += f"{status} *{t.name}* — {time_str}\n"
        msg += f"   Категория: {t.category or '—'} | Важность: {t.priority}\n\n"

    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['complete'])
def ask_complete_task(message: Message):
    user = get_user_by_telegram_id(message.chat.id)
    if not user:
        bot.reply_to(message, "❌ Сначала зарегистрируйтесь через /register")
        return

    tasks = get_uncompleted_tasks_for_today(user.id)
    if not tasks:
        bot.send_message(message.chat.id, "✅ На сегодня нет незавершённых задач.")
        return

    keyboard = get_complete_task_keyboard(tasks)
    bot.send_message(message.chat.id, "Выберите задачу для отметки:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("complete_"))
def complete_task_callback(call: CallbackQuery):
    task_id = int(call.data.split("_")[1])
    user = get_user_by_telegram_id(call.message.chat.id)
    if not user:
        bot.answer_callback_query(call.id, "Пользователь не найден")
        return

    if mark_task_complete(task_id, user.id):
        bot.edit_message_text(
            "✅ Задача отмечена выполненной!",
            call.message.chat.id,
            call.message.message_id
        )
        bot.answer_callback_query(call.id, "Готово!")
    else:
        bot.answer_callback_query(call.id, "Не удалось отметить. Возможно, задача уже выполнена.")