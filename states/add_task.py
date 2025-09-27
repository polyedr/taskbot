# app/states/add_task.py
from aiogram.fsm.state import State, StatesGroup


class AddTaskStates(StatesGroup):
    choosing_category = State()
    typing_title = State()
    typing_deadline = State()
    confirm = State()
