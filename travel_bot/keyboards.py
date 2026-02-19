"""Inline keyboards for the bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def search_result_keyboard(offset: int = 0, has_more: bool = True) -> InlineKeyboardMarkup:
    """
    Buttons: "Больше вариантов" (if has_more), "Сохранить", "Новый поиск".
    callback_data includes offset for pagination (next 5 from same set).
    """
    buttons = []
    if has_more:
        buttons.append([InlineKeyboardButton("Больше вариантов", callback_data=f"more:{offset}")])
    buttons.append([
        InlineKeyboardButton("Сохранить", callback_data="save"),
        InlineKeyboardButton("Новый поиск", callback_data="new_search"),
    ])
    return InlineKeyboardMarkup(buttons)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Single button to start search."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Новый поиск", callback_data="new_search")],
    ])
