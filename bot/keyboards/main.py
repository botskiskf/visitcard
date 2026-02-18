from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Тренировки"), KeyboardButton(text="Прогресс")],
        ],
        resize_keyboard=True,
    )
