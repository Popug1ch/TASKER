from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    """Главное меню с кнопками"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("📋 Задачи сегодня", callback_data="menu_tasks"),
        InlineKeyboardButton("🎉 События сегодня", callback_data="menu_events"),
        InlineKeyboardButton("⏰ Дедлайны (24ч)", callback_data="menu_deadlines"),
        InlineKeyboardButton("✅ Отметить выполненной", callback_data="menu_complete"),
        InlineKeyboardButton("❓ Помощь", callback_data="menu_help"),
    ]
    keyboard.add(*buttons)
    return keyboard