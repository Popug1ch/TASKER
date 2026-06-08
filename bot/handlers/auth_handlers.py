from telebot.types import Message
from bot.loader import bot
from bot.utils.db_helpers import register_user_by_email_password
from bot.states.auth_states import AuthStates
from telebot.states.sync.context import StateContext


@bot.message_handler(commands=["register"])
def start_register(message: Message, state: StateContext):
    state.set(AuthStates.waiting_email)
    bot.send_message(
        message.chat.id,
        "📧 Введите ваш email, который вы использовали при регистрации на сайте:",
    )


@bot.message_handler(state=AuthStates.waiting_email)
def get_email(message: Message, state: StateContext):
    email = message.text.strip()
    state.add_data(email=email)
    state.set(AuthStates.waiting_password)
    bot.send_message(message.chat.id, "🔑 Введите пароль:")


@bot.message_handler(state=AuthStates.waiting_password)
def get_password(message: Message, state: StateContext):
    password = message.text.strip()
    with state.data() as data:
        email = data.get("email")
    user_id = message.from_user.id
    if register_user_by_email_password(user_id, email, password):
        bot.send_message(
            message.chat.id,
            "✅ Вы успешно привязали Telegram аккаунт! Теперь вы можете получать уведомления и управлять задачами.",
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Неверный email или пароль. Попробуйте ещё раз /register",
        )
    state.delete()
