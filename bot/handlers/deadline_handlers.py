from datetime import datetime

from telebot.types import Message
from bot.loader import bot
from bot.utils.db_helpers import get_user_by_telegram_id, get_upcoming_deadlines


@bot.message_handler(commands=["deadlines"])
def show_deadlines(message: Message):
    user = get_user_by_telegram_id(message.chat.id)
    if not user:
        bot.reply_to(message, "❌ Сначала зарегистрируйтесь через /register")
        return

    deadlines = get_upcoming_deadlines(user.id)
    if not deadlines:
        bot.send_message(message.chat.id, "✅ Нет дедлайнов на ближайшие 24 часа.")
        return

    msg = "⏰ *Дедлайны на ближайшие 24 часа:*\n\n"
    for d in deadlines:
        remaining = d.deadline_time - datetime.now()
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        msg += f"💣 *{d.name}*\n"
        msg += f"   Осталось: {hours} ч {minutes} мин\n"
        msg += f"   Сгорает: {d.deadline_time.strftime('%H:%M, %d.%m.%Y')}\n\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
