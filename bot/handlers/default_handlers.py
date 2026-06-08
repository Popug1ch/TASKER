from telebot.types import Message
from bot.loader import bot
from bot.utils.db_helpers import get_user_by_telegram_id

from telebot.types import Message
from bot.loader import bot
from bot.utils.db_helpers import get_user_by_telegram_id
from bot.keyboards.main_menu import get_main_menu_keyboard

from telebot.types import Message
from bot.loader import bot
from bot.utils.db_helpers import get_user_by_telegram_id
from bot.keyboards.main_menu import get_main_menu_keyboard


@bot.message_handler(commands=["start", "help"])
def start_command(message: Message):
    user = get_user_by_telegram_id(message.chat.id)
    if user:
        text = (
            f"👋 С возвращением, {user.username}!\n\n"
            "📌 *Доступные команды:*\n"
            "/tasks – список задач на сегодня\n"
            "/events – список событий на сегодня\n"
            "/deadlines – дедлайны на ближайшие 24 часа\n"
            "/complete – отметить задачу выполненной\n"
            "/register – привязать аккаунт (если ещё не привязан)\n"
            "/help – показать это сообщение\n\n"
            "👇 Или используйте кнопки ниже:"
        )
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        text = (
            "👋 Добро пожаловать в Таскер-бот!\n\n"
            "🔐 *Чтобы начать, нужно привязать Telegram к вашему аккаунту на сайте.*\n\n"
            "Используйте команду:\n"
            "`/register email@example.com ваш_пароль`\n\n"
            "После привязки вы сможете просматривать задачи, события, дедлайны и отмечать задачи выполненными.\n\n"
            "📌 Список команд:\n"
            "/register – привязать аккаунт\n"
            "/help – помощь\n"
            "/start – главное меню"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=["help"])
def help_command(message: Message):
    help_text = (
        "📖 *Справка по командам:*\n\n"
        "/register email пароль — привязать аккаунт Таскер к Telegram\n"
        "/tasks — список задач на сегодня\n"
        "/events — список событий на сегодня\n"
        "/deadlines — дедлайны на ближайшие 24 часа\n"
        "/complete — отметить задачу как выполненную\n"
        "/start — приветствие\n"
        "/help — эта справка"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")
