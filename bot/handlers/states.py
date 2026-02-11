from aiogram.fsm.state import State, StatesGroup


class LocationStates(StatesGroup):
    waiting_city = State()


class ReminderStates(StatesGroup):
    waiting_offset = State()


class TasbehStates(StatesGroup):
    waiting_goal = State()


class SettingsStates(StatesGroup):
    waiting_offset = State()


class SilentHoursStates(StatesGroup):
    waiting_hours = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()


class MosquesStates(StatesGroup):
    waiting_location = State()
