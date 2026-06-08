from telebot.types import CallbackQuery
from bot.loader import bot
from bot.handlers import task_handlers, event_handlers, deadline_handlers

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def menu_callback(call: CallbackQuery):
    action = call.data.split("_")[1]
    if action == "tasks":
        # Вызываем команду /tasks
        task_handlers.show_tasks(call.message)
    elif action == "events":
        event_handlers.show_events(call.message)
    elif action == "deadlines":
        deadline_handlers.show_deadlines(call.message)
    elif action == "complete":
        task_handlers.ask_complete_task(call.message)
    elif action == "help":
        # Отправляем справку
        from bot.handlers.default_handlers import help_command
        help_command(call.message)
    bot.answer_callback_query(call.id)