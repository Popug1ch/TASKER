from telebot.types import Message
from bot.loader import bot
from bot.utils.db_helpers import get_user_by_telegram_id, get_today_events


@bot.message_handler(commands=["events"])
def show_events(message: Message):
    user = get_user_by_telegram_id(message.chat.id)
    if not user:
        bot.reply_to(message, "❌ Сначала зарегистрируйтесь через /register")
        return

    events = get_today_events(user.id)
    if not events:
        bot.send_message(message.chat.id, "📭 Сегодня нет событий.")
        return

    msg = "🎉 *События сегодня:*\n\n"
    for ev in events:
        msg += f"• {ev.name}\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
