from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def progress_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Добавить вес", callback_data="progress:add_weight"),
        InlineKeyboardButton(text="Добавить замер", callback_data="progress:add_measurement"),
    )
    builder.row(
        InlineKeyboardButton(text="Добавить достижение", callback_data="progress:add_achievement"),
    )
    builder.row(
        InlineKeyboardButton(text="История прогресса", callback_data="progress:history"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="main"),
    )
    return builder.as_markup()


def progress_history_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="progress:menu"),
    )
    return builder.as_markup()
