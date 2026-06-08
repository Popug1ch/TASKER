from telebot.states import State, StatesGroup


class AuthStates(StatesGroup):
    waiting_email = State()
    waiting_password = State()
