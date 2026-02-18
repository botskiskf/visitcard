from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.storage import (
    get_or_create_user,
    add_weight,
    add_measurement,
    add_achievement,
    get_weight_history,
    get_measurements_history,
    get_achievements_history,
)
from bot.keyboards.progress import progress_menu_kb, progress_history_kb
from bot.keyboards.main import get_main_menu_kb

router = Router(name="progress")


class ProgressStates(StatesGroup):
    weight = State()
    measurement_name = State()
    measurement_value = State()
    measurement_unit = State()
    achievement_text = State()


def _format_date(iso_str: str) -> str:
    try:
        date_part = iso_str.split("T")[0]
        y, m, d = date_part.split("-")
        return f"{d}.{m}.{y}"
    except Exception:
        return iso_str


@router.message(F.text == "Прогресс")
async def show_progress_menu(message: Message) -> None:
    if message.from_user:
        await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
    await message.answer(
        "Отслеживание прогресса. Выбери действие:",
        reply_markup=progress_menu_kb(),
    )


@router.callback_query(F.data == "progress:menu")
async def callback_progress_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "Отслеживание прогресса. Выбери действие:",
        reply_markup=progress_menu_kb(),
    )


@router.callback_query(F.data == "progress:add_weight")
async def start_add_weight(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProgressStates.weight)
    await callback.message.edit_text("Введи вес в кг (например: 72.5):")


@router.message(ProgressStates.weight, F.text)
async def save_weight(message: Message, state: FSMContext) -> None:
    try:
        value = float(message.text.replace(",", "."))
        if value <= 0 or value > 300:
            await message.answer("Введи корректный вес (0–300 кг):")
            return
    except ValueError:
        await message.answer("Введи число, например: 72.5")
        return
    user_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await add_weight(user_id, value)
    await state.clear()
    await message.answer(f"Вес {value} кг сохранён.")
    await message.answer("Отслеживание прогресса:", reply_markup=progress_menu_kb())


@router.callback_query(F.data == "progress:add_measurement")
async def start_add_measurement(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProgressStates.measurement_name)
    await callback.message.edit_text("Введи название замера (например: Объём талии):")


@router.message(ProgressStates.measurement_name, F.text)
async def step_measurement_name(message: Message, state: FSMContext) -> None:
    await state.update_data(measurement_name=message.text.strip())
    await state.set_state(ProgressStates.measurement_value)
    await message.answer("Введи значение (число):")


@router.message(ProgressStates.measurement_value, F.text)
async def step_measurement_value(message: Message, state: FSMContext) -> None:
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введи число:")
        return
    await state.update_data(measurement_value=value)
    await state.set_state(ProgressStates.measurement_unit)
    await message.answer("Введи единицу измерения (например: см, кг):")


@router.message(ProgressStates.measurement_unit, F.text)
async def save_measurement(message: Message, state: FSMContext) -> None:
    unit = message.text.strip() or "ед."
    data = await state.get_data()
    name = data.get("measurement_name", "Замер")
    value = data.get("measurement_value", 0)
    user_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await add_measurement(user_id, name, value, unit)
    await state.clear()
    await message.answer(f"Замер «{name}»: {value} {unit} — сохранён.")
    await message.answer("Отслеживание прогресса:", reply_markup=progress_menu_kb())


@router.callback_query(F.data == "progress:add_achievement")
async def start_add_achievement(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProgressStates.achievement_text)
    await callback.message.edit_text("Напиши своё достижение (например: Пробежал 5 км):")


@router.message(ProgressStates.achievement_text, F.text)
async def save_achievement(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        await message.answer("Введи текст достижения:")
        return
    user_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await add_achievement(user_id, text)
    await state.clear()
    await message.answer("Достижение сохранено.")
    await message.answer("Отслеживание прогресса:", reply_markup=progress_menu_kb())


@router.callback_query(F.data == "progress:history")
async def show_history(callback: CallbackQuery) -> None:
    await callback.answer()
    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    lines = []
    weights = await get_weight_history(user_id, limit=10)
    if weights:
        lines.append("Вес (последние записи):")
        for val, dt in weights:
            lines.append(f"  {val} кг — {_format_date(dt)}")
        lines.append("")
    measurements = await get_measurements_history(user_id, limit=10)
    if measurements:
        lines.append("Замеры:")
        for name, val, unit, dt in measurements:
            lines.append(f"  {name}: {val} {unit} — {_format_date(dt)}")
        lines.append("")
    achievements = await get_achievements_history(user_id, limit=10)
    if achievements:
        lines.append("Достижения:")
        for text, dt in achievements:
            lines.append(f"  {text} — {_format_date(dt)}")
    if not lines:
        text = "Пока нет записей. Добавь вес, замер или достижение."
    else:
        text = "\n".join(lines).strip()
    await callback.message.edit_text(
        text,
        reply_markup=progress_history_kb(),
    )
