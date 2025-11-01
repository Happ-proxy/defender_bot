from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    answering_quiz = State()
    completed = State()
