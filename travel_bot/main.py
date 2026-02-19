"""Telegram bot: flights + hotels search with AI combos. Run with: python main.py"""
import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    ALLOWED_TELEGRAM_IDS,
    CURRENCY,
    DEFAULT_ORIGIN_AIRPORT,
    TELEGRAM_TOKEN,
)
from database import get_history, init_db, save_search
from keyboards import main_menu_keyboard, search_result_keyboard
from utils import parse_query

# In-memory store of last search result per user (for "Больше вариантов" and "Сохранить")
_last_search: dict[int, dict[str, Any]] = {}

CURRENCY_SYM = "€" if CURRENCY == "EUR" else CURRENCY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _check_access(user_id: int) -> bool:
    if not ALLOWED_TELEGRAM_IDS:
        return True
    return user_id in ALLOWED_TELEGRAM_IDS


def _format_duration(mins: int) -> str:
    h, m = divmod(mins, 60)
    if m:
        return f"{h}ч {m}м"
    return f"{h}ч"


def _build_result_text(
    parsed: Any,
    flights: list[dict],
    hotels: list[dict],
    combos_data: dict,
    offset: int,
    nights: int,
) -> str:
    """Build Markdown message for one page (5 items each)."""
    origin = parsed.origin_iata
    dest = parsed.destination
    start = offset
    end_f = min(start + 5, len(flights))
    end_h = min(start + 5, len(hotels))
    slice_f = flights[start:end_f]
    slice_h = hotels[start:end_h]

    lines = [
        f"🛫 <b>ПЕРЕЛЁТЫ</b> ({origin}→{dest}):",
        "",
    ]
    for i, f in enumerate(slice_f, start=start + 1):
        stops = "прямой" if f.get("stops") == 0 else f"{f.get('stops')} пересадка"
        lines.append(
            f"{f.get('airline', '?')} {f.get('price_per_person', 0)}{CURRENCY_SYM}×{parsed.adults} = "
            f"{f.get('total_price', 0)}{CURRENCY_SYM} ({_format_duration(f.get('duration_min', 0))}, {stops}) ⭐{f.get('rating', 0)}"
        )
    lines.extend(["", "🏨 <b>ОТЕЛИ</b> (топ, центр):", ""])
    for i, h in enumerate(slice_h, start=start + 1):
        disc = f" (-{h.get('discount')}% СКИДКА!)" if h.get("discount") else ""
        lines.append(
            f"{'🔥 ' if h.get('discount') else ''}{i}. {h.get('name', '?')} {h.get('stars', 4)}★ — "
            f"{h.get('price_per_night', 0)}{CURRENCY_SYM}/ночь{disc} ⭐{h.get('rating', 0)}"
        )
    lines.extend(["", "💰 <b>ЛУЧШИЕ КОМБО:</b>", ""])
    for i, c in enumerate(combos_data.get("best_combos", [])[:2], start=1):
        medal = "🥇" if i == 1 else "🥈"
        label = c.get("label", "")
        total = c.get("total", 0)
        lines.append(f"{medal} {label} = {total}{CURRENCY_SYM}")
    rec = combos_data.get("recommendation", "")
    if rec:
        lines.extend(["", rec])
    return "\n".join(lines)


async def do_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query_text: str) -> None:
    """Run search, store result, send formatted message + keyboard."""
    user_id = update.effective_user.id if update.effective_user else 0
    parsed = parse_query(query_text, DEFAULT_ORIGIN_AIRPORT)
    if not parsed:
        await update.message.reply_text(
            "Не удалось разобрать запрос. Укажите город, даты (например 15-22 июля), "
            "количество человек, звёздность отеля и при желании бюджет. Пример:\n"
            "Барселона 15-22 июля, 2 человека, 4*, бюджет 1500€"
        )
        return

    from search_flights import search_flights
    from search_hotels import search_hotels
    from ai_analyzer import analyze_combos

    # Nights from dates
    from datetime import datetime
    d1 = datetime.strptime(parsed.outbound_date, "%Y-%m-%d")
    d2 = datetime.strptime(parsed.return_date, "%Y-%m-%d")
    nights = max(1, (d2 - d1).days)

    flights = search_flights(
        parsed.origin_iata,
        parsed.destination_iata,
        parsed.outbound_date,
        parsed.return_date,
        parsed.adults,
    )
    hotels = search_hotels(
        parsed.destination,
        parsed.outbound_date,
        parsed.return_date,
        parsed.adults,
        parsed.stars,
    )
    combos_data = analyze_combos(flights, hotels, nights, parsed.budget)

    _last_search[user_id] = {
        "query_text": query_text,
        "parsed": parsed,
        "flights": flights,
        "hotels": hotels,
        "combos": combos_data,
        "nights": nights,
    }

    text = _build_result_text(parsed, flights, hotels, combos_data, offset=0, nights=nights)
    has_more = len(flights) > 5 or len(hotels) > 5
    keyboard = search_result_keyboard(offset=5, has_more=has_more)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def do_search_safe(update: Update, context: ContextTypes.DEFAULT_TYPE, query_text: str) -> None:
    """Run search and send; use plain text if Markdown fails."""
    try:
        await do_search(update, context, query_text)
    except Exception as e:
        logger.exception("Search or send failed: %s", e)
        await update.message.reply_text(
            "Поиск выполнен, но форматирование не удалось. Проверьте историю или повторите запрос."
        )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _check_access(update.effective_user.id):
        await update.message.reply_text("Бот только для личного использования.")
        return
    await update.message.reply_text(
        "Привет! Я помогу подобрать перелёты и отели по лучшим ценам с AI-анализом комбо.\n\n"
        "Пример запроса:\n"
        "Барселона 15-22 июля, 2 человека, 4*, бюджет 1500€\n\n"
        "Команды: /search — поиск, /history — история, /settings — настройки, /help — помощь.",
        reply_markup=main_menu_keyboard(),
    )


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _check_access(update.effective_user.id):
        await update.message.reply_text("Бот только для личного использования.")
        return
    await update.message.reply_text(
        "Напишите запрос одним сообщением. Пример:\n"
        "Барселона 15-22 июля, 2 человека, 4*, бюджет 1500€"
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _check_access(update.effective_user.id):
        await update.message.reply_text("Бот только для личного использования.")
        return
    user_id = update.effective_user.id
    rows = get_history(user_id, limit=15)
    if not rows:
        await update.message.reply_text("История поисков пуста.")
        return
    lines = ["История поисков (можно повторить, отправив тот же запрос):", ""]
    for _id, q, created in rows:
        lines.append(f"• {q}")
    await update.message.reply_text("\n".join(lines))


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _check_access(update.effective_user.id):
        await update.message.reply_text("Бот только для личного использования.")
        return
    await update.message.reply_text(
        f"Текущие настройки:\n"
        f"• Аэропорт вылета: {DEFAULT_ORIGIN_AIRPORT}\n"
        f"• Валюта: {CURRENCY}\n\n"
        "Чтобы изменить — отредактируйте файл .env в папке бота и перезапустите бота."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _check_access(update.effective_user.id):
        await update.message.reply_text("Бот только для личного использования.")
        return
    await update.message.reply_text(
        "Команды:\n"
        "/start — приветствие и пример\n"
        "/search — начать поиск (затем введите запрос)\n"
        "/history — последние поиски\n"
        "/settings — аэропорт вылета и валюта\n"
        "/help — эта справка\n\n"
        "Можно просто написать запрос текстом, например: Барселона 15-22 июля 2ч 4*"
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    if not _check_access(update.effective_user.id):
        await update.message.reply_text("Бот только для личного использования.")
        return
    text = update.message.text.strip()
    if text.startswith("/"):
        return
    await do_search_safe(update, context, text)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return
    user_id = update.effective_user.id if update.effective_user else 0
    if not _check_access(user_id):
        await update.callback_query.answer("Доступ запрещён.")
        return
    data = update.callback_query.data
    await update.callback_query.answer()

    if data == "new_search":
        await update.callback_query.edit_message_text(
            "Напишите новый запрос. Пример: Барселона 15-22 июля, 2 человека, 4*, бюджет 1500€",
            reply_markup=main_menu_keyboard(),
        )
        return

    last = _last_search.get(user_id)
    if not last:
        await update.callback_query.edit_message_text("Нет последнего поиска. Отправьте новый запрос.")
        return

    if data == "save":
        save_search(user_id, last["query_text"])
        await update.callback_query.edit_message_text("Запрос сохранён в историю.", reply_markup=main_menu_keyboard())
        return

    if data.startswith("more:"):
        try:
            offset = int(data.split(":")[1])
        except (IndexError, ValueError):
            offset = 5
        parsed = last["parsed"]
        flights = last["flights"]
        hotels = last["hotels"]
        combos = last["combos"]
        nights = last["nights"]
        text = _build_result_text(parsed, flights, hotels, combos, offset=offset, nights=nights)
        has_more = len(flights) > offset + 5 or len(hotels) > offset + 5
        keyboard = search_result_keyboard(offset=offset + 5, has_more=has_more)
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=keyboard
            )
        except Exception:
            await update.callback_query.edit_message_text(
                "Не удалось обновить сообщение. Отправьте новый запрос.",
                reply_markup=main_menu_keyboard(),
            )


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise SystemExit("Задайте TELEGRAM_TOKEN в .env")
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_callback))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
