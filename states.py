# states.py
from aiogram.fsm.state import StatesGroup, State

class ProcessStates(StatesGroup):
    waiting_number = State()
    waiting_file = State()

class AdminStates(StatesGroup):
    waiting_user_id_to_add = State()
