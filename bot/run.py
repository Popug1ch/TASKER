from bot.loader import bot
from bot.handlers import (
    default_handlers,
    auth_handlers,
    task_handlers,
    event_handlers,
    deadline_handlers,
    menu_handlers
)
import logging
from bot.scheduler import start_scheduler
from telebot import custom_filters
from telebot.states.sync.middleware import StateMiddleware
from bot.handlers import menu_handlers

logging.basicConfig(level=logging.INFO)
def main():
    try:
        bot.add_custom_filter(custom_filters.StateFilter(bot))
        bot.setup_middleware(StateMiddleware(bot))
        start_scheduler()
        print("Бот запущен и готов к работе.")
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()