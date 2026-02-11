from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def menu_reply_keyboard(text: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
    )


def location_request_keyboard(text: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
