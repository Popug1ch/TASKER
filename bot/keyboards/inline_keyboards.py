from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_complete_task_keyboard(tasks):
    """Клавиатура для выбора задачи (отметка выполненной)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            f"☑️ {task.name} ({task.start_time.strftime('%H:%M')})",
            callback_data=f"complete_{task.id}"
        ))
    return keyboard

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard